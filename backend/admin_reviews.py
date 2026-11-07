
from datetime import datetime, timezone

import mysql.connector

from bson import ObjectId
from bson.errors import InvalidId

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from pymongo.errors import PyMongoError

from auth import role_required, valid_csrf
from db import get_db_connection
from mongo_db import get_reviews_collection


admin_reviews_bp = Blueprint(
    "admin_reviews",
    __name__
)

ALLOWED_STATUSES = (
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
)


# ==========================================
# FETCH FACILITY NAMES FROM MYSQL
# ==========================================

def get_facility_names():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT facility_id, facility_name
            FROM facilities
            ORDER BY facility_id
            """
        )

        rows = cursor.fetchall()

        return {
            row["facility_id"]: row["facility_name"]
            for row in rows
        }

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ==========================================
# ADMIN FEEDBACK DASHBOARD
# ==========================================

@admin_reviews_bp.route(
    "/admin/reviews",
    methods=["GET"]
)
@role_required("ADMIN")
def feedback_dashboard():

    try:
        collection = get_reviews_collection()

        # Read MongoDB review documents
        reviews = list(
            collection.find().sort(
                "created_at", -1
            )
        )

        # Get facility names from MySQL
        facility_names = get_facility_names()

        # Attach facility names for display
        for review in reviews:
            review["facility_name"] = (
                facility_names.get(
                    review.get("facility_id"),
                    "Unknown Facility"
                )
            )

        # MongoDB aggregation for statuses
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "$ifNull": [
                            "$status",
                            "OPEN"
                        ]
                    },
                    "count": {"$sum": 1}
                }
            }
        ]

        result = list(
            collection.aggregate(pipeline)
        )

        status_counts = {
            "OPEN": 0,
            "IN_PROGRESS": 0,
            "RESOLVED": 0,
        }

        for item in result:
            if item["_id"] in status_counts:
                status_counts[item["_id"]] = (
                    item["count"]
                )

        return render_template(
            "admin_reviews.html",
            reviews=reviews,
            total_reviews=len(reviews),
            status_counts=status_counts,
            allowed_statuses=ALLOWED_STATUSES,
        )

    except (mysql.connector.Error, PyMongoError):

        abort(
            503,
            description=(
                "Unable to load feedback dashboard."
            )
        )


# ==========================================
# UPDATE COMPLAINT STATUS
# ==========================================

@admin_reviews_bp.route(
    "/admin/reviews/<review_id>/status",
    methods=["POST"]
)
@role_required("ADMIN")
def update_feedback_status(review_id):

    if not valid_csrf():
        abort(
            400,
            description="Invalid form token."
        )

    new_status = request.form.get(
        "status", ""
    ).strip()

    if new_status not in ALLOWED_STATUSES:

        flash(
            "Invalid feedback status.",
            "error"
        )

        return redirect(
            url_for(
                "admin_reviews.feedback_dashboard"
            )
        )

    try:
        object_id = ObjectId(review_id)

    except (InvalidId, TypeError):
        abort(404)

    try:
        collection = get_reviews_collection()

        result = collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now(
                        timezone.utc
                    ),
                    "reviewed_by": session["user_id"],
                }
            }
        )

        if result.matched_count == 0:
            abort(404)

        flash(
            "Feedback status updated successfully!",
            "success"
        )

    except PyMongoError:

        flash(
            "Unable to update feedback status.",
            "error"
        )

    return redirect(
        url_for(
            "admin_reviews.feedback_dashboard"
        )
    )
