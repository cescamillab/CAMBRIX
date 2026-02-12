from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import get_connection

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates"
)

@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        session.clear()
        
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM usuarios WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["rol"] = user["rol"]

            return redirect(url_for("dashboard.home"))
        else:
            error = "Usuario o contraseña incorrectos"

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
