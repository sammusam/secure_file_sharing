from pymongo import MongoClient
from app.config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["secure_file_share"]
users_collection = db["users"]
files_collection = db["files"]
