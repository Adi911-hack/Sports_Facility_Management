
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


reviews_bp = Blueprint("reviews", __name__)

CATEGORIES = (
    "General",
    "Maintenance",
    "Cleanliness",
    "Equipment",
    "Staff",
)


# ==========================================
# LOOK UP FACILITY FROM MYSQL
# ==========================================

def get_facility(facility_id):
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
                f.status,
                s.sport_name
            FROM facilities AS f
            JOIN sports AS s
                ON f.sport_id = s.sport_id
            WHERE f.facility_id = %s
            """,
            (facility_id,)
        )

        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ==========================================
# VALIDATE REVIEW INPUT
# ==========================================

def read_review_form():
    rating_str = request.form.get("rating", "").strip()

    category = request.form.get(
        "category", ""
    ).strip()

    comment = request.form.get(
        "comment", ""
    ).strip()

    try:
        rating = int(rating_str)
    except ValueError:
        return None, "Choose a valid rating."

    if rating not in (1, 2, 3, 4, 5):
        return None, "Rating must be between 1 and 5."

    if category not in CATEGORIES:
        return None, "Choose a valid review category."

    if not 5 <= len(comment) <= 500:
        return (
            None,
            "Comment must contain 5 to 500 characters."
        )

    return {
        "rating": rating,
        "category": category,
        "comment": comment,
    }, None


# ==========================================
# READ REVIEWS
# ==========================================

@reviews_bp.route(
    "/reviews/<int:facility_id>",
    methods=["GET"]
)
def facility_reviews(facility_id):

    try:
        facility = get_facility(facility_id)

        if facility is None:
            abort(404)

        collection = get_reviews_collection()

        reviews = list(
            collection.find({
                "facility_id": facility_id
            }).sort("created_at", -1)
        )

        total = len(reviews)

        average_rating = (
            round(
                sum(r["rating"] for r in reviews) / total,
                1
            )
            if total else None
        )

        return render_template(
            "reviews.html",
            facility=facility,
            reviews=reviews,
            average_rating=average_rating,
            total_reviews=total,
            categories=CATEGORIES,
            current_user_id=session.get("user_id"),
        )

    except (mysql.connector.Error, PyMongoError):
        abort(503, description="Reviews unavailable.")


# ==========================================
# CREATE A REVIEW
# ==========================================

@reviews_bp.route(
    "/reviews/<int:facility_id>/create",
    methods=["POST"]
)
@role_required("STUDENT")
def create_review(facility_id):

    if not valid_csrf():
        abort(400, description="Invalid form token.")

    values, error = read_review_form()

    if error:
        flash(error, "error")
        return redirect(
            url_for(
                "reviews.facility_reviews",
                facility_id=facility_id
            )
        )

    try:
        facility = get_facility(facility_id)

        if facility is None:
            abort(404)

        collection = get_reviews_collection()

        collection.insert_one({
            "facility_id": facility_id,
            "user_id": session["user_id"],
            "rating": values["rating"],
            "category": values["category"],
            "comment": values["comment"],
            "status": "OPEN",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

        flash("Review submitted successfully!", "success")

    except (mysql.connector.Error, PyMongoError):
        flash("Unable to save review.", "error")

    return redirect(
        url_for(
            "reviews.facility_reviews",
            facility_id=facility_id
        )
    )


# ==========================================
# UPDATE YOUR OWN REVIEW
# ==========================================

@reviews_bp.route(
    "/reviews/<int:facility_id>/<review_id>/update",
    methods=["POST"]
)
@role_required("STUDENT")
def update_review(facility_id, review_id):

    if not valid_csrf():
        abort(400, description="Invalid form token.")

    try:
        object_id = ObjectId(review_id)
    except (InvalidId, TypeError):
        abort(404)

    values, error = read_review_form()

    if error:
        flash(error, "error")
        return redirect(
            url_for(
                "reviews.facility_reviews",
                facility_id=facility_id
            )
        )

    try:
        collection = get_reviews_collection()

        result = collection.update_one(
            {
                "_id": object_id,
                "facility_id": facility_id,
                "user_id": session["user_id"],
            },
            {
                "$set": {
                    "rating": values["rating"],
                    "category": values["category"],
                    "comment": values["comment"],
                    "updated_at": datetime.now(timezone.utc),
                }
            }
        )

        if result.matched_count == 0:
            abort(404)

        flash("Review updated successfully!", "success")

    except PyMongoError:
        flash("Unable to update review.", "error")

    return redirect(
        url_for(
            "reviews.facility_reviews",
            facility_id=facility_id
        )
    )


# ==========================================
# DELETE YOUR OWN REVIEW
# ==========================================

@reviews_bp.route(
    "/reviews/<int:facility_id>/<review_id>/delete",
    methods=["POST"]
)
@role_required("STUDENT")
def delete_review(facility_id, review_id):

    if not valid_csrf():
        abort(400, description="Invalid form token.")

    try:
        object_id = ObjectId(review_id)
    except (InvalidId, TypeError):
        abort(404)

    try:
        collection = get_reviews_collection()

        result = collection.delete_one({
            "_id": object_id,
            "facility_id": facility_id,
            "user_id": session["user_id"],
        })

        if result.deleted_count == 0:
            abort(404)

        flash("Review deleted successfully!", "success")

    except PyMongoError:
        flash("Unable to delete review.", "error")

    return redirect(
        url_for(
            "reviews.facility_reviews",
            facility_id=facility_id
        )
    )
