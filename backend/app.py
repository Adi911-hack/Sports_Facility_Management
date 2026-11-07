
import os
import secrets

from datetime import date, datetime, timedelta
from pathlib import Path
from reviews import reviews_bp

from admin_reviews import admin_reviews_bp
from analytics_api import analytics_bp

import mysql.connector

from dotenv import load_dotenv

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from db import get_db_connection
from auth import (
    auth_bp,
    login_required,
    role_required,
    valid_csrf,
)


# ==========================================
# FLASK APPLICATION CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")

if not secret_key or len(secret_key) < 32:
    raise RuntimeError(
        "SECRET_KEY is missing or too short. "
        "Add a secure SECRET_KEY to your .env file."
    )

app.config["SECRET_KEY"] = secret_key

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# False is appropriate only for local HTTP development.
# Set True when deploying over HTTPS.
app.config["SESSION_COOKIE_SECURE"] = False

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=4)


# ==========================================
# REGISTER AUTHENTICATION BLUEPRINT
# ==========================================

app.register_blueprint(auth_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(admin_reviews_bp)
app.register_blueprint(analytics_bp)

# ==========================================
# SESSION AND CSRF SETUP
# ==========================================

@app.before_request
def prepare_session():

    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    if "user_id" in session:
        session.permanent = True


@app.context_processor
def inject_template_variables():

    return {
        "current_user_name": session.get("full_name"),
        "current_user_role": session.get("role"),
        "csrf_token": session.get("csrf_token"),
    }


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "application": "ARENA",
        "message": "Flask server is running",
    })


# ==========================================
# FACILITIES API
# ==========================================

@app.route("/api/facilities", methods=["GET"])
def get_facilities():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                f.facility_id,
                f.facility_name,
                f.location,
                f.capacity,
                f.status,
                s.sport_id,
                s.sport_name
            FROM facilities AS f
            JOIN sports AS s
                ON f.sport_id = s.sport_id
            ORDER BY f.facility_id
            """
        )

        facilities = cursor.fetchall()

        return jsonify({
            "success": True,
            "total": len(facilities),
            "facilities": facilities,
        })

    except mysql.connector.Error:

        app.logger.exception(
            "Error fetching sports facilities"
        )

        return jsonify({
            "success": False,
            "message": "Unable to load facilities",
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ==========================================
# STUDENT DASHBOARD
# ==========================================

@app.route("/dashboard")
@login_required
def dashboard():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        user_id = session["user_id"]

        # Fetch current logged-in user
        cursor.execute(
            """
            SELECT
                user_id,
                full_name,
                email,
                role
            FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None:
            session.clear()

            flash(
                "Your account could not be found. "
                "Please log in again.",
                "error"
            )

            return redirect(url_for("auth.login"))

        # Fetch this user's booking history
        cursor.execute(
            """
            SELECT
                booking_id,
                facility_id,
                facility_name,
                sport_name,
                booking_date,
                start_time,
                end_time,
                status
            FROM vw_booking_details
            WHERE user_id = %s
            ORDER BY booking_date DESC,
                     start_time DESC
            """,
            (user_id,)
        )

        bookings = cursor.fetchall()

        return render_template(
            "dashboard.html",
            user=user,
            bookings=bookings,
            total_bookings=len(bookings),
        )

    except mysql.connector.Error:

        app.logger.exception(
            "Student dashboard database error"
        )

        return "Unable to load dashboard.", 500

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route("/admin")
@role_required("ADMIN")
def admin_dashboard():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        # Dashboard statistics
        cursor.execute(
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM users
                    WHERE role = 'STUDENT'
                ) AS total_students,

                (
                    SELECT COUNT(*)
                    FROM facilities
                ) AS total_facilities,

                (
                    SELECT COUNT(*)
                    FROM bookings
                ) AS total_bookings,

                (
                    SELECT COUNT(*)
                    FROM tournaments
                ) AS total_tournaments
            """
        )

        stats = cursor.fetchone()

        # Facility management overview
        cursor.execute(
            """
            SELECT
                f.facility_id,
                f.facility_name,
                s.sport_name,
                f.location,
                f.status
            FROM facilities AS f
            JOIN sports AS s
                ON f.sport_id = s.sport_id
            ORDER BY f.facility_id
            """
        )

        facilities = cursor.fetchall()

        return render_template(
            "admin.html",
            stats=stats,
            facilities=facilities,
        )

    except mysql.connector.Error:

        app.logger.exception(
            "Admin dashboard database error"
        )

        return "Unable to load admin dashboard.", 500

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ==========================================
# BOOK A SPORTS FACILITY
# ==========================================

@app.route(
    "/book/<int:facility_id>",
    methods=["GET", "POST"]
)
@role_required("STUDENT")
def book_facility(facility_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        # Dictionary cursor for SELECT operations
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                facility_id,
                facility_name,
                status
            FROM facilities
            WHERE facility_id = %s
            """,
            (facility_id,)
        )

        facility = cursor.fetchone()

        if facility is None:
            abort(404)

        # ----------------------------------
        # SHOW BOOKING FORM
        # ----------------------------------

        if request.method == "GET":

            return render_template(
                "book.html",
                facility=facility,
                today=date.today().isoformat(),
            )

        # ----------------------------------
        # VALIDATE CSRF TOKEN
        # ----------------------------------

        if not valid_csrf():
            abort(
                400,
                description="Invalid booking request."
            )

        # Get user ID from authenticated session
        # Never accept user ID from a browser form.
        user_id = session["user_id"]

        booking_date_str = request.form.get(
            "booking_date", ""
        )

        start_time_str = request.form.get(
            "start_time", ""
        )

        end_time_str = request.form.get(
            "end_time", ""
        )

        # ----------------------------------
        # PARSE BOOKING DATE AND TIME
        # ----------------------------------

        try:

            booking_date = date.fromisoformat(
                booking_date_str
            )

            start_time = datetime.strptime(
                start_time_str,
                "%H:%M"
            ).time()

            end_time = datetime.strptime(
                end_time_str,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Please enter a valid date and time.",
                "error"
            )

            return redirect(
                url_for(
                    "book_facility",
                    facility_id=facility_id
                )
            )

        # ----------------------------------
        # VALIDATE BOOKING DETAILS
        # ----------------------------------

        now = datetime.now()

        if booking_date < now.date():

            flash(
                "You cannot book a past date.",
                "error"
            )

            return redirect(
                url_for(
                    "book_facility",
                    facility_id=facility_id
                )
            )

        if start_time >= end_time:

            flash(
                "End time must be after start time.",
                "error"
            )

            return redirect(
                url_for(
                    "book_facility",
                    facility_id=facility_id
                )
            )

        if (
            booking_date == now.date()
            and start_time <= now.time()
        ):

            flash(
                "Choose a future starting time.",
                "error"
            )

            return redirect(
                url_for(
                    "book_facility",
                    facility_id=facility_id
                )
            )

        if facility["status"] != "AVAILABLE":

            flash(
                "This facility is currently unavailable.",
                "error"
            )

            return redirect(
                url_for(
                    "book_facility",
                    facility_id=facility_id
                )
            )

        # ----------------------------------
        # CALL MYSQL STORED PROCEDURE
        # ----------------------------------

        # IMPORTANT FIX:
        # Close the dictionary cursor and create
        # a regular cursor for callproc().
        #
        # A regular cursor returns the procedure
        # parameters as a sequence, allowing
        # us to read the OUT value at index 5.

        cursor.close()

        cursor = None

        cursor = connection.cursor()

        result = cursor.callproc(
            "sp_create_booking",
            [
                user_id,
                facility_id,
                booking_date,
                start_time,
                end_time,
                0,
            ]
        )

        booking_id = result[5]

        # sp_create_booking commits internally.
        # Do not insert the booking again.

        flash(
            f"Booking #{booking_id} confirmed successfully!",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    # ----------------------------------
    # MYSQL BOOKING ERRORS
    # ----------------------------------

    except mysql.connector.Error as exc:

        app.logger.warning(
            "Booking database error: %s",
            exc
        )

        if connection is not None:
            try:
                connection.rollback()
            except mysql.connector.Error:
                pass

        expected_errors = {
            "Invalid booking date or time",
            "Facility not found",
            "Facility is unavailable",
            "Valid student required",
            "Booking slot already occupied",
            "Facility reserved for a match",
        }

        if (
            exc.errno == 1644
            and exc.msg in expected_errors
        ):

            message = exc.msg

        else:

            app.logger.exception(
                "Unexpected booking database error"
            )

            message = (
                "Unable to complete booking. "
                "Please try again."
            )

        flash(message, "error")

        return redirect(
            url_for(
                "book_facility",
                facility_id=facility_id
            )
        )

    # ----------------------------------
    # CLEANUP
    # ----------------------------------

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()




# ==========================================
# CANCEL A SPORTS FACILITY BOOKING
# ==========================================

@app.route(
    "/bookings/<int:booking_id>/cancel",
    methods=["POST"]
)
@role_required("STUDENT")
def cancel_booking(booking_id):

    # Validate the form's CSRF token
    if not valid_csrf():
        abort(
            400,
            description="Invalid cancellation request."
        )

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        # Use a regular cursor to call the procedure
        cursor = connection.cursor()

        # Get the logged-in user from the session
        # Never accept user_id from the form
        user_id = session["user_id"]

        # The stored procedure checks ownership,
        # booking status, and cancellation deadline.
        cursor.callproc(
            "sp_cancel_booking",
            [
                booking_id,
                user_id
            ]
        )

        # The procedure commits internally.
        flash(
            f"Booking #{booking_id} cancelled successfully!",
            "success"
        )

    except mysql.connector.Error as exc:

        app.logger.warning(
            "Booking cancellation failed: %s",
            exc
        )

        if connection is not None:
            try:
                connection.rollback()
            except mysql.connector.Error:
                pass

        expected_errors = {
            "Booking not found",
            "Not authorized to cancel booking",
            "Only confirmed bookings can be cancelled",
            "Booking has already started",
        }

        if (
            exc.errno == 1644
            and exc.msg in expected_errors
        ):
            message = exc.msg
        else:
            app.logger.exception(
                "Unexpected cancellation database error"
            )
            message = (
                "Unable to cancel booking. "
                "Please try again."
            )

        flash(message, "error")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

    return redirect(url_for("dashboard"))


# ==========================================
# APPLICATION ENTRY POINT
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )
