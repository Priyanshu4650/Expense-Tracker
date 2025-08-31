from fastapi import HTTPException
from database import get_database
from pymongo.errors import DuplicateKeyError

db = get_database()

def create_category(name: str):
    try:
        db.categories.insert_one({"name": name})
        return {"message": "Category created successfully"}
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Category already exists")

def get_categories():
    categories = list(db.categories.find({}, {"name": 1, "_id": 0}).sort("name", 1))
    return [category["name"] for category in categories]