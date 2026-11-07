
from mongo_db import get_reviews_collection
from pymongo.errors import PyMongoError


def show_facility_ratings():
    collection = get_reviews_collection()

    pipeline = [
        {
            "$group": {
                "_id": "$facility_id",
                "total_reviews": {"$sum": 1},
                "average_rating": {
                    "$avg": "$rating"
                },
                "highest_rating": {
                    "$max": "$rating"
                },
                "lowest_rating": {
                    "$min": "$rating"
                }
            }
        },
        {
            "$sort": {
                "average_rating": -1,
                "total_reviews": -1
            }
        }
    ]

    results = list(
        collection.aggregate(pipeline)
    )

    print("\nARENA FACILITY RATING ANALYTICS")
    print("-" * 55)

    if not results:
        print("No facility reviews available.")
        return

    for result in results:
        print(
            f"Facility ID: {result['_id']} | "
            f"Reviews: {result['total_reviews']} | "
            f"Average: {result['average_rating']:.2f}/5 | "
            f"Highest: {result['highest_rating']} | "
            f"Lowest: {result['lowest_rating']}"
        )


def show_feedback_categories():
    collection = get_reviews_collection()

    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "total": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "total": -1
            }
        }
    ]

    print("\nFEEDBACK CATEGORY DISTRIBUTION")
    print("-" * 55)

    for result in collection.aggregate(pipeline):
        print(
            f"{result['_id']}: "
            f"{result['total']} review(s)"
        )


if __name__ == "__main__":
    try:
        show_facility_ratings()
        show_feedback_categories()
    except PyMongoError as error:
        print("MongoDB analytics failed:", error)
