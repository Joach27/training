from flask import Flask, render_template,request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date,datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

app.secret_key = "ma_cle_super_secrete_123"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = \
'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    done = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date,nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id',ondelete = 'CASCADE'), nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(15), nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy=True, cascade="all, delete-orphan")

    def set_password(self,password):
        self.password = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password, password)



@app.route("/",methods=["GET","POST"])
def home():
     # Vérifier que l'utilisateur est connecté
    if "user_id" not in session:
        flash("Veuillez vous connecter pour accéder à vos tâches", "error")
        return redirect(url_for("login")) # Redirige vers login si pas connecté

    # Récupérer l'utilisateur connecté depuis la BDD par sa clé primaire
    user = User.query.get(session["user_id"])
     
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        due_date_str = request.form.get("due_date")
        # Convertir la string en objet date
        if due_date_str:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        else:
            due_date = None

        # Créer une tâche en Base
        new_task = Task(title = title,description = description,due_date = due_date,done = False,user_id = user.id)
    
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("home"))
    
    # Récupérer uniquement les tâches de l'utilisateur connecté
    tasks = Task.query.filter_by(user_id=user.id).order_by(Task.id.desc()).all() # ← .desc() = plus récent en premier 
    return render_template('home.html',tasks = tasks, user = user)


@app.route("/delete/<int:task_id>",methods=["POST","GET"])
def delete(task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    task = Task.query.get_or_404(task_id)

    if task.user_id != session["user_id"]:
        flash("Action non autorisée", "error")
        return redirect(url_for("home"))
    
    db.session.delete(task)
    db.session.commit()

    flash("Tâche supprimée", "success")

    return redirect(url_for("home"))    


@app.route("/toggle/<int:task_id>",methods = ["POST"])
def toggle_done(task_id):
    if "user_id" not in session:
        redirect(url_for("login"))
    task = Task.query.get_or_404(task_id)

    # Vérifier que la tache appartient à l'utilisateur qui est connecté
    if task and task.user_id == session["user_id"]:
        task.done = not task.done
        db.session.commit()
    return redirect(url_for("home"))

@app.route("/edit/<int:task_id>",methods=["GET","POST"])
def update_task(task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))
     
    task = Task.query.get_or_404(task_id)

    if task.user_id != session["user_id"]:
        flash("Action non autorisée", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        task.title = request.form.get("title")
        task.description = request.form.get("description")
        due_date_str = request.form.get("due_date")
        if due_date_str:
            task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        else:
            task.due_date = None
        
        db.session.commit()

        flash("Tâche mise à jour", "success")

        return redirect(url_for("home"))

    return render_template("edit_task.html", task=task)


#Inscription
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":

        full_name = request.form.get("full_name")
        email     = request.form.get("email")
        password  = request.form.get("password")

        # Vérifier si un utilisateur avec cet email existe déjà
        existing_user = User.query.filter_by(email = email).first()

        if existing_user:
            flash("Ce nom d'utilisateur existe déjà.", "error")
            return redirect(url_for("login"))
        else:
            # Créer le nouvel utilisateur
            new_user = User( full_name=full_name,email=email,password=password)
            new_user.set_password(password)
            db.session.add(new_user) 
            db.session.commit()

             # Connecter automatiquement l'utilisateur après inscription
            session["user_id"] = new_user.id
            flash("Compte créé avec succès !", "success")

            return redirect(url_for('home'))
    return render_template("register.html")


#Connexion
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":
        email     = request.form.get("email")
        password  = request.form.get("password")
    
        # Chercher l'utilisateur par email et mot de passe
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password) :
            session["user_id"] = user.id
            flash("Connecté avec succès !", "success")
            return redirect(url_for("home"))
        else:
             flash("Identifiants invalides", "error")
        
    return render_template("login.html")
    

# Deconnexion
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))



if (__name__ == '__main__'):
    #with app.app_context():
          #db.drop_all()   
          #db.create_all()

    app.run(debug = True)