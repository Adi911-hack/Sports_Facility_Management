
import hashlib
import hmac
import logging
import os
import re
import secrets

from functools import wraps

import mysql.connector

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from db import get_db_connection


auth_bp = Blueprint("auth", __name__)

logger = logging.getLogger(__name__)


# Password hashing compatible with our existing
# PBKDF2 demonstration accounts.
def hash_password(password):
    iterations = 600_000
    salt = os.urandom(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations
    )

    return (
        f"pbkdf2:sha256:{iterations}$"
        f"{salt.hex()}${hashed.hex()}"
    )


def verify_password(password, stored_hash):
    try:
        algorithm, salt_hex, hash_hex = (
            stored_hash.split("$")
        )

        prefix, method, iterations = (
            algorithm.split(":")
        )

        if prefix != "pbkdf2" or method != "sha256":
            return False

        iterations = int(iterations)

        if not 100_000 <= iterations <= 2_000_000:
            return False

        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return hmac.compare_digest(
            actual,
            expected
        )

    except (ValueError, TypeError, AttributeError):
        return False


# Protect pages requiring login.
def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")

            return redirect(
                url_for("auth.login")
            )

        return function(*args, **kwargs)

    return wrapper


# Verify submitted forms came from our site.
def valid_csrf():
    submitted = request.form.get(
        "csrf_token", ""
    )

    expected = session.get(
        "csrf_token", ""
    )

    return (
        bool(submitted)
        and bool(expected)
        and hmac.compare_digest(
            submitted,
            expected
        )
    )


# --------------------------------------
# STUDENT REGISTRATION
# --------------------------------------

@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "GET":
        return render_template(
            "register.html"
        )

    if not valid_csrf():
        flash(
            "Invalid form request.",
            "error"
        )
        return redirect(
            url_for("auth.register")
        )

    full_name = request.form.get(
        "full_name", ""
    ).strip()

    email = request.form.get(
        "email", ""
    ).strip().lower()

    password = request.form.get(
        "password", ""
    )

    confirm_password = request.form.get(
        "confirm_password", ""
    )

    if not 2 <= len(full_name) <= 100:
        flash(
            "Enter a valid full name.",
            "error"
        )
        return redirect(
            url_for("auth.register")
        )

    if len(email) > 150 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email
    ):
        flash(
            "Enter a valid email address.",
            "error"
        )
        return redirect(
            url_for("auth.register")
        )

    if not 10 <= len(password) <= 128:
        flash(
            "Password must contain 10-128 characters.",
            "error"
        )
        return redirect(
            url_for("auth.register")
        )

    if password != confirm_password:
        flash(
            "Passwords do not match.",
            "error"
        )
        return redirect(
            url_for("auth.register")
        )

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users
                (full_name, email, password_hash, role)
            VALUES
                (%s, %s, %s, 'STUDENT')
            """,
            (
                full_name,
                email,
                hash_password(password)
            )
        )

        connection.commit()

    except mysql.connector.IntegrityError as error:
        if connection:
            connection.rollback()

        if error.errno == 1062:
            flash(
                "Email already registered.",
                "error"
            )
        else:
            logger.exception(
                "Registration integrity error"
            )
            flash(
                "Registration failed.",
                "error"
            )

        return redirect(
            url_for("auth.register")
        )

    except mysql.connector.Error:
        if connection:
            connection.rollback()

        logger.exception(
            "Registration database error"
        )

        flash(
            "Registration is temporarily unavailable.",
            "error"
        )

        return redirect(
            url_for("auth.register")
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

    flash(
        "Account created successfully! Please log in.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )


# --------------------------------------
# STUDENT LOGIN
# --------------------------------------

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "GET":
        return render_template(
            "login.html"
        )

    if not valid_csrf():
        flash(
            "Invalid form request.",
            "error"
        )
        return redirect(
            url_for("auth.login")
        )

    email = request.form.get(
        "email", ""
    ).strip().lower()

    password = request.form.get(
        "password", ""
    )

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                user_id,
                full_name,
                email,
                password_hash,
                role
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

    except mysql.connector.Error:
        logger.exception(
            "Login database error"
        )

        flash(
            "Login service temporarily unavailable.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

    if not user or not verify_password(
        password,
        user["password_hash"]
    ):
        flash(
            "Invalid email or password.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    session.clear()

    session["user_id"] = user["user_id"]
    session["full_name"] = user["full_name"]
    session["role"] = user["role"]

    session["csrf_token"] = (
        secrets.token_urlsafe(32)
    )

    return redirect(
        url_for("dashboard")
    )


# --------------------------------------
# LOGOUT
# --------------------------------------

@auth_bp.route(
    "/logout",
    methods=["POST"]
)
@login_required
def logout():

    if not valid_csrf():
        flash(
            "Invalid logout request.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("home")
    )



# --------------------------------------
# ROLE-BASED ACCESS CONTROL
# --------------------------------------

def role_required(required_role):
    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            if "user_id" not in session:
                flash("Please log in first.", "error")
                return redirect(url_for("auth.login"))

            connection = None
            cursor = None

            try:
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)

                cursor.execute(
                    """
                    SELECT role
                    FROM users
                    WHERE user_id = %s
                    """,
                    (session["user_id"],)
                )

                user = cursor.fetchone()

            except mysql.connector.Error:
                logger.exception(
                    "Authorization database error"
                )

                abort(503)

            finally:
                if cursor is not None:
                    cursor.close()

                if connection is not None:
                    connection.close()

            if user is None:
                session.clear()
                return redirect(url_for("auth.login"))

            if user["role"] != required_role:
                abort(403)

            return function(*args, **kwargs)

        return wrapper

    return decorator
