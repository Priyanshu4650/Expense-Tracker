from pymongo import MongoClient
import os

MONGODB_URL = "mongodb+srv://priyanshu022017_db_user:Dwx4cTAON4Ey7Fmb@cluster0.5pcoyiq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "expense_tracker"

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]

def get_database():
    return db

def init_database():
    """Initialize MongoDB collections and default data"""
    try:
        # Create collections if they don't exist
        collections = ['users', 'expenses', 'categories', 'monthly_plans', 'budgets']
        
        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
        
        # Insert default categories if collection is empty
        if db.categories.count_documents({}) == 0:
            default_categories = [
                {"name": "Rent"},
                {"name": "Food"}, 
                {"name": "Travelling"}
            ]
            db.categories.insert_many(default_categories)
        
        # Create indexes for better performance
        db.users.create_index("username", unique=True)
        db.expenses.create_index("user_id")
        db.monthly_plans.create_index([("month", 1), ("user_id", 1)], unique=True)
        db.budgets.create_index([("category", 1), ("month", 1), ("user_id", 1)], unique=True)
        
        print("MongoDB database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e