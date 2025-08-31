from database import get_database
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from fastapi import HTTPException

db = get_database()

def validate_object_id(user_id: str):
    try:
        return ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=401, detail="Invalid user session. Please login again.")

def set_monthly_plan(month: str, income: float, budgets: dict, user_id: str):
    user_obj_id = validate_object_id(user_id)
    
    # Set income
    db.monthly_plans.replace_one(
        {"month": month, "user_id": user_obj_id},
        {
            "month": month,
            "income": income,
            "user_id": user_obj_id,
            "created_at": datetime.now()
        },
        upsert=True
    )
    
    # Set budgets
    for category, amount in budgets.items():
        db.budgets.replace_one(
            {"category": category, "month": month, "user_id": user_obj_id},
            {
                "category": category,
                "amount": amount,
                "month": month,
                "user_id": user_obj_id
            },
            upsert=True
        )
    
    return {"message": "Monthly plan set successfully"}

def get_monthly_plan(month: str, user_id: str):
    user_obj_id = validate_object_id(user_id)
    
    # Get income
    income_doc = db.monthly_plans.find_one({"month": month, "user_id": user_obj_id})
    income = income_doc["income"] if income_doc else 0
    
    # Get budgets
    budget_docs = list(db.budgets.find({"month": month, "user_id": user_obj_id}))
    budgets = {doc["category"]: doc["amount"] for doc in budget_docs}
    
    return {
        "income": income,
        "budgets": budgets,
        "total_planned": sum(budgets.values())
    }

def get_budget_status(month: str, user_id: str):
    user_obj_id = validate_object_id(user_id)
    
    # Get budgets
    budget_docs = list(db.budgets.find({"month": month, "user_id": user_obj_id}))
    budgets = {doc["category"]: doc["amount"] for doc in budget_docs}
    
    # Get actual spending for the month
    spending_pipeline = [
        {
            "$match": {
                "user_id": user_obj_id,
                "$expr": {
                    "$eq": [
                        {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}},
                        month
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$category",
                "spent": {"$sum": "$amount"}
            }
        }
    ]
    
    spending_docs = list(db.expenses.aggregate(spending_pipeline))
    spending = {doc["_id"]: doc["spent"] for doc in spending_docs}
    
    status = {}
    for category, budget in budgets.items():
        spent = spending.get(category, 0)
        status[category] = {
            "budget": budget,
            "spent": spent,
            "remaining": budget - spent,
            "percentage": (spent / budget * 100) if budget > 0 else 0
        }
    
    return status