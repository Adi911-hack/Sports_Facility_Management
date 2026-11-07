
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017/"
)

MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "arena_reviews"
)


client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)


def get_mongo_database():
    return client[MONGO_DB_NAME]


def get_reviews_collection():
    database = get_mongo_database()
    return database["facility_reviews"]


def test_mongo_connection():
    client.admin.command("ping")
    return True


if __name__ == "__main__":
    try:
        test_mongo_connection()

        print("MongoDB connected successfully!")
        print("Database:", MONGO_DB_NAME)

    except Exception as error:
        print("MongoDB connection failed:", error)
