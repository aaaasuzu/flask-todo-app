from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date
from werkzeug.security import generate_password_hash,check_password_hash
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key")

def init_db():
    conn = sqlite3.connect("todo.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT,
        deadline TEXT,
        priority INTEGER,
        done INTEGER DEFAULT 0,
        user_id INTEGER
    )
    """)

    conn.commit()
    conn.close()


init_db()

def get_db():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    return conn

#ログイン必須デコレーター
def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args,**kwargs)
    return decorated_function

@app.route("/", methods=["GET","POST"])
@login_required
def index():

   
    conn = get_db()
    user_id = session["user_id"]

    if request.method == "POST":

        task = request.form["task"]
        deadline = request.form["deadline"]
        priority = request.form["priority"]

       #　バリデーション
        if task.strip() == "" or len(task) > 100:
            return redirect("/")
        if priority not in ["1","2","3"]:
            return redirect("/")
        

        conn.execute(
            "INSERT INTO tasks (task,deadline,priority,user_id) VALUES (?,?,?,?)",
            (task, deadline, priority, user_id)
            )
        conn.commit()

    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id=? ORDER BY priority DESC",
        (user_id,)
    ).fetchall()

    conn.close()

    today = date.today().isoformat()

    return render_template("index.html", tasks=tasks, today=today)


@app.route("/delete/<int:id>")
@login_required
def delete(id):

    conn = get_db()

    conn.execute(
        "DELETE FROM tasks WHERE id=? AND user_id=? " ,
        (id,session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/done/<int:id>", methods=["POST"])
@login_required
def done(id):

    conn = get_db()

    conn.execute(
        "UPDATE tasks SET done = NOT done WHERE id=? AND user_id=?",
        (id,session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        
        conn = get_db()
        hashed_password = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            (username,hashed_password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"],password):
            session["user_id"] = user["id"]
            return redirect("/")
        else:
            print("ログインに失敗しました")
        

        
    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=10000)