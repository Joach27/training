import os

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'tasks.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = 'une_cle_secrete'

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)


@app.route("/", methods=["GET", "POST"])
def home():
    if "user_id" not in session:
        flash("Veuillez vous connecter pour accéder à vos tâches", "error")
        return redirect(url_for("login"))
    
    user = User.query.get(session["user_id"])

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        due_date_str = request.form["due_date"]
        if due_date_str:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        else:
            due_date = None

        new_task = Task(
            title=title,
            description=description,
            due_date=due_date,
            done=False,
            user_id=user.id
        )

        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for("home")) 

    tasks = Task.query.filter_by(user_id=user.id).all()
    return render_template("home.html", tasks=tasks, user=user)


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_done(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    task = Task.query.get_or_404(task_id)

    # Vérifier que la tache appartient à l'utilisateur qui est connecté 
    if task and task.user_id == session["user_id"]:
        task.done = not task.done
        db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
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

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def update_task(task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    task = Task.query.get_or_404(task_id)

    if task.user_id != session["user_id"]:
        flash("Action non autorisée", "error")
        return redirect(url_for("home"))

    if request.method == "POST":

        task.title = request.form["title"]
        task.description = request.form["description"]

        due_date_str = request.form["due_date"]

        if due_date_str:
            task.due_date = datetime.strptime(
                due_date_str,
                "%Y-%m-%d"
            ).date()
        else:
            task.due_date = None

        db.session.commit()

        flash("Tâche mise à jour", "success")

        return redirect(url_for("home"))

    return render_template("edit_task.html", task=task)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]  

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username ou email déjà utilisé", "error")
            return redirect(url_for("login"))

        new_user = User(username=username, email=email, password=password)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
    
        session["user_id"] = new_user.id
        flash("Compte créé avec succès !", "success")

        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("Connecté avec succès !", "success")
            return redirect(url_for("home"))

        flash("Identifiants invalides", "error")

        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for("login"))

@app.route("/test-relation")
def test_relation():
    # 1. Créer un utilisateur
    new_user = User(username="testuser", email="test@test.com", password="hashed_pass")
    db.session.add(new_user)
    db.session.commit()  # Obligatoire pour générer l'ID avant de l'utiliser

    # 2. Créer une tâche et la lier
    new_task = Task(
        title="Vérifier la relation",
        description="Test de liaison user <-> task",
        due_date=date.today(),
        user_id=new_user.id  # Ou: owner=new_user
    )
    db.session.add(new_task)
    db.session.commit()

    # 3. Vérification bidirectionnelle
    fetched_user = User.query.get(new_user.id)
    fetched_task = Task.query.get(new_task.id)

    # Ce qui doit fonctionner :
    print("Tasks du user :", [t.title for t in fetched_user.tasks])
    print("Propriétaire de la task :", fetched_task.owner.username)

    return jsonify({
        "user_tasks": [t.title for t in fetched_user.tasks],
        "task_owner": fetched_task.owner.username
    }), 200



if __name__ == "__main__":
    app.run(debug=True)

