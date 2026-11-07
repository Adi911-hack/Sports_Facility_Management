
import mysql.connector

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
)

from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
)

from pymongo.errors import PyMongoError

from auth import verify_password
from db import get_db_connection
from mongo_db import get_reviews_collection


analytics_bp = Blueprint(
    "analytics",
    __name__
)

TOKEN_LIFETIME = 30 * 60


def get_token_serializer():
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt="arena-nextjs-admin-analytics-v1"
    )


# =========================================
# ADMIN LOGIN FOR NEXT.JS
# =========================================

@analytics_bp.route(
    "/api/analytics/login",
    methods=["POST"]
)
def analytics_login():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid request."
        }), 400

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = data.get("password", "")

    if (
        not isinstance(password, str)
        or not email
        or not password
        or len(email) > 150
        or len(password) > 128
    ):
        return jsonify({
            "error": "Invalid credentials."
        }), 401

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                user_id,
                full_name,
                password_hash,
                role
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if (
            user is None
            or user["role"] != "ADMIN"
            or not verify_password(
                password,
                user["password_hash"]
            )
        ):
            return jsonify({
                "error": "Invalid credentials."
            }), 401

        serializer = get_token_serializer()

        token = serializer.dumps({
            "user_id": user["user_id"]
        })

        return jsonify({
            "success": True,
            "token": token,
            "expires_in": TOKEN_LIFETIME,
            "admin_name": user["full_name"],
        })

    except mysql.connector.Error:
        current_app.logger.exception(
            "Analytics login database error"
        )

        return jsonify({
            "error": "Login service unavailable."
        }), 503

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# =========================================
# VERIFY ADMIN TOKEN AND DATABASE ROLE
# =========================================

def get_authorized_admin():

    header = request.headers.get(
        "Authorization", ""
    )

    scheme, separator, token = header.partition(" ")

    if (
        not separator
        or scheme.lower() != "bearer"
        or not token
    ):
        return None

    try:
        payload = get_token_serializer().loads(
            token,
            max_age=TOKEN_LIFETIME
        )

        user_id = payload.get("user_id")

        if type(user_id) is not int:
            return None

    except (BadSignature, AttributeError, TypeError):
        return None

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT user_id, full_name, role
            FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None or user["role"] != "ADMIN":
            return None

        return user

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# =========================================
# LIVE MYSQL + MONGODB ANALYTICS
# =========================================

@analytics_bp.route(
    "/api/analytics/summary",
    methods=["GET"]
)
def analytics_summary():

    connection = None
    cursor = None

    try:
        admin = get_authorized_admin()

        if admin is None:
            return jsonify({
                "error": "Admin authorization required."
            }), 401

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Overall MySQL statistics
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
                    FROM bookings
                    WHERE status = 'CONFIRMED'
                ) AS confirmed_bookings,

                (
                    SELECT COUNT(*)
                    FROM tournaments
                ) AS total_tournaments
            """
        )

        overview = cursor.fetchone()

        # Booking volume by sport
        cursor.execute(
            """
            SELECT
                s.sport_name,
                COUNT(b.booking_id) AS booking_count
            FROM sports s
            JOIN facilities f
                ON f.sport_id = s.sport_id
            LEFT JOIN bookings b
                ON b.facility_id = f.facility_id
            GROUP BY
                s.sport_id,
                s.sport_name
            ORDER BY
                booking_count DESC,
                s.sport_name
            """
        )

        popular_sports = cursor.fetchall()

        # Booking counts by facility
        cursor.execute(
            """
            SELECT
                f.facility_id,
                f.facility_name,
                COUNT(b.booking_id) AS booking_count
            FROM facilities f
            LEFT JOIN bookings b
                ON b.facility_id = f.facility_id
            GROUP BY
                f.facility_id,
                f.facility_name
            ORDER BY
                booking_count DESC,
                f.facility_id
            """
        )

        facility_usage = cursor.fetchall()

        # MongoDB review statistics
        collection = get_reviews_collection()

        review_pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_reviews": {"$sum": 1},
                    "average_rating": {"$avg": "$rating"}
                }
            }
        ]

        review_result = list(
            collection.aggregate(review_pipeline)
        )

        if review_result:
            total_reviews = review_result[0][
                "total_reviews"
            ]

            average_rating = round(
                review_result[0]["average_rating"],
                2
            )
        else:
            total_reviews = 0
            average_rating = None

        status_pipeline = [
            {
                "$group": {
                    "_id": {
                        "$ifNull": ["$status", "OPEN"]
                    },
                    "count": {"$sum": 1}
                }
            }
        ]

        feedback_status = {
            "OPEN": 0,
            "IN_PROGRESS": 0,
            "RESOLVED": 0,
        }

        for item in collection.aggregate(
            status_pipeline
        ):
            status = item["_id"]

            if status in feedback_status:
                feedback_status[status] = item["count"]

        return jsonify({
            "success": True,
            "admin_name": admin["full_name"],
            "overview": {
                **overview,
                "total_reviews": total_reviews,
                "average_rating": average_rating,
            },
            "popular_sports": popular_sports,
            "facility_usage": facility_usage,
            "feedback_status": feedback_status,
        })

    except (
        mysql.connector.Error,
        PyMongoError
    ):
        current_app.logger.exception(
            "Analytics database query failed"
        )

        return jsonify({
            "error": "Analytics temporarily unavailable."
        }), 503

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()
