from datetime import datetime
from fastapi import HTTPException
from database import get_database
from bson import ObjectId
from bson.errors import InvalidId

db = get_database()

def validate_object_id(user_id: str):
    try:
        return ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=401, detail="Invalid user session. Please login again.")

def create_expense(category: str, amount: float, description: str, payment_date: str, user_id: str):
    user_obj_id = validate_object_id(user_id)
    payment_date = payment_date if payment_date else datetime.now().strftime('%Y-%m-%d')
    
    expense_doc = {
        "category": category,
        "amount": amount,
        "description": description,
        "user_id": user_obj_id,
        "payment_date": payment_date,
        "created_at": datetime.now()
    }
    
    result = db.expenses.insert_one(expense_doc)
    return {"id": str(result.inserted_id), "message": "Expense created successfully"}

def get_expenses(user_id: str):
    user_obj_id = validate_object_id(user_id)
    expenses = list(db.expenses.find({"user_id": user_obj_id}).sort("created_at", -1))
    
    for expense in expenses:
        expense["id"] = str(expense["_id"])
        expense["user_id"] = str(expense["user_id"])
        expense["created_at"] = expense["created_at"].isoformat()
        # Ensure payment_date is included
        if "payment_date" not in expense:
            expense["payment_date"] = expense["created_at"][:10]  # Use created_at date as fallback
        del expense["_id"]
    
    return expenses

def update_expense(expense_id: str, category: str, amount: float, description: str, payment_date: str, user_id: str):
    user_obj_id = validate_object_id(user_id)
    payment_date = payment_date if payment_date else datetime.now().strftime('%Y-%m-%d')
    
    result = db.expenses.update_one(
        {"_id": ObjectId(expense_id), "user_id": user_obj_id},
        {"$set": {
            "category": category,
            "amount": amount,
            "description": description,
            "payment_date": payment_date
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    return {"message": "Expense updated successfully"}

def delete_expense(expense_id: str, user_id: str):
    user_obj_id = validate_object_id(user_id)
    result = db.expenses.delete_one({"_id": ObjectId(expense_id), "user_id": user_obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    return {"message": "Expense deleted successfully"}

def get_expenses_summary(user_id: str):
    user_obj_id = validate_object_id(user_id)
    pipeline = [
        {"$match": {"user_id": user_obj_id}},
        {"$group": {
            "_id": "$category",
            "total": {"$sum": "$amount"}
        }}
    ]
    
    summary = list(db.expenses.aggregate(pipeline))
    category_totals = {item["_id"]: item["total"] for item in summary}
    
    total_pipeline = [
        {"$match": {"user_id": user_obj_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    
    total_result = list(db.expenses.aggregate(total_pipeline))
    total = total_result[0]["total"] if total_result else 0
    
    return {
        "total": total,
        "categories": category_totals
    }

def get_expenses_analytics(user_id: str):
    user_obj_id = validate_object_id(user_id)
    # Monthly trends
    monthly_pipeline = [
        {"$match": {"user_id": user_obj_id}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}},
            "total": {"$sum": "$amount"}
        }},
        {"$sort": {"_id": -1}},
        {"$limit": 6}
    ]
    
    monthly_trends = [{"month": item["_id"], "total": item["total"]} 
                     for item in db.expenses.aggregate(monthly_pipeline)]
    
    # Category breakdown
    category_pipeline = [
        {"$match": {"user_id": user_obj_id}},
        {"$group": {
            "_id": "$category",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total": -1}}
    ]
    
    category_breakdown = [{"category": item["_id"], "total": item["total"], "count": item["count"]} 
                         for item in db.expenses.aggregate(category_pipeline)]
    
    # Recent activity (last 7 days)
    from datetime import timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    recent_pipeline = [
        {"$match": {"user_id": user_obj_id, "created_at": {"$gte": seven_days_ago}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "total": {"$sum": "$amount"}
        }},
        {"$sort": {"_id": -1}}
    ]
    
    recent_activity = [{"date": item["_id"], "total": item["total"]} 
                      for item in db.expenses.aggregate(recent_pipeline)]
    
    # Top expenses
    top_expenses = list(db.expenses.find({"user_id": user_obj_id})
                       .sort("amount", -1).limit(5))
    
    for expense in top_expenses:
        expense["date"] = expense["created_at"].isoformat()
        del expense["_id"]
        del expense["user_id"]
        del expense["created_at"]
    
    return {
        "monthly_trends": monthly_trends,
        "category_breakdown": category_breakdown,
        "recent_activity": recent_activity,
        "top_expenses": top_expenses
    }