from flask import Blueprint, render_template, request, redirect, url_for, session
from app.services.auth_service import AuthService

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

        result = AuthService.login(username, password)

        if result["success"]:
            session["user_id"] = result["user_id"]
            session["username"] = result["username"]
            session["rol"] = result["rol"]

            return redirect(url_for("dashboard.home"))
        else:
            error = result["error"]

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

