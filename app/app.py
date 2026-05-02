from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    done = db.Column(db.Boolean, default=False)

@app.route("/", methods=["GET", "POST"])
def home():
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
            done=False
        )

        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for("home")) 

    tasks = Task.query.all()
    return render_template("home.html", tasks=tasks)


@app.route("/toggle/<int:task_id>")
def toggle(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = not task.done
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete/<int:task_id>")
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("home"))    

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == "POST":
        task.title = request.form["title"]
        task.description = request.form["description"]

        due_date_str = request.form["due_date"]
        if due_date_str:
            task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        else:
            task.due_date = None

        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", task=task)
()
# with app.app_context():
#     db.create_all()

# if __name__ == "__main__":
#     app.run(debug=True)

