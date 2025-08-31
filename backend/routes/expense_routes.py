from fastapi import APIRouter, Depends
from typing import List
from models.expense import ExpenseCreate, Expense
from services.expense_service import create_expense, get_expenses, update_expense, delete_expense, get_expenses_summary, get_expenses_analytics
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])

@router.post("", response_model=dict)
async def create_expense_route(expense: ExpenseCreate, user_id: str = Depends(get_current_user)):
    return create_expense(expense.category, expense.amount, expense.description, expense.payment_date, user_id)

@router.get("", response_model=List[Expense])
async def get_expenses_route(user_id: str = Depends(get_current_user)):
    return get_expenses(user_id)

@router.put("/{expense_id}")
async def update_expense_route(expense_id: str, expense: ExpenseCreate, user_id: str = Depends(get_current_user)):
    return update_expense(expense_id, expense.category, expense.amount, expense.description, expense.payment_date, user_id)

@router.delete("/{expense_id}")
async def delete_expense_route(expense_id: str, user_id: str = Depends(get_current_user)):
    return delete_expense(expense_id, user_id)

@router.get("/summary")
async def get_expenses_summary_route(user_id: str = Depends(get_current_user)):
    return get_expenses_summary(user_id)

@router.get("/analytics")
async def get_expenses_analytics_route(user_id: str = Depends(get_current_user)):
    return get_expenses_analytics(user_id)