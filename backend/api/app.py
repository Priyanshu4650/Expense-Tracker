from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
import sys
import os
import sqlite3
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db_connection, init_database

SECRET_KEY = "expense_tracker_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer()

router = APIRouter()

# Initialize database on startup
init_database()

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ExpenseCreate(BaseModel):
    category: str
    amount: float
    description: str = ""

class Expense(BaseModel):
    id: int
    category: str
    amount: float
    description: str
    created_at: str

class CategoryCreate(BaseModel):
    name: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/register")
async def register(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password and create user
    password_hash = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (user.username, password_hash)
    )
    
    conn.commit()
    conn.close()
    return {"message": "User created successfully"}

@router.post("/login")
async def login(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (user.username,))
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data or not bcrypt.checkpw(user.password.encode('utf-8'), user_data[1]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user_data[0])})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/categories", response_model=dict)
async def create_category(category: CategoryCreate, user_id: str = Depends(verify_token)):
    """Create a new category"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (category.name,))
        conn.commit()
        return {"message": "Category created successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Category already exists")
    finally:
        conn.close()

@router.get("/categories")
async def get_categories(user_id: str = Depends(verify_token)):
    """Get all categories"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM categories ORDER BY name")
    categories = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in categories]

@router.post("/expenses", response_model=dict)
async def create_expense(expense: ExpenseCreate, user_id: str = Depends(verify_token)):
    """Create a new expense"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO expenses (category, amount, description, user_id) VALUES (?, ?, ?, ?)",
        (expense.category, expense.amount, expense.description, user_id)
    )
    
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": expense_id, "message": "Expense created successfully"}

@router.get("/expenses", response_model=List[Expense])
async def get_expenses(user_id: str = Depends(verify_token)):
    """Get all expenses"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM expenses WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    expenses = cursor.fetchall()
    conn.close()
    
    return [dict(expense) for expense in expenses]

@router.put("/expenses/{expense_id}")
async def update_expense(expense_id: int, expense: ExpenseCreate, user_id: str = Depends(verify_token)):
    """Update an expense"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE expenses SET category = ?, amount = ?, description = ? WHERE id = ? AND user_id = ?",
        (expense.category, expense.amount, expense.description, expense_id, user_id)
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Expense not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Expense updated successfully"}

@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, user_id: str = Depends(verify_token)):
    """Delete an expense"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Expense not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Expense deleted successfully"}

@router.get("/expenses/summary")
async def get_expenses_summary(user_id: str = Depends(verify_token)):
    """Get expenses summary by category"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses 
        GROUP BY category
    """)
    
    summary = cursor.fetchall()
    
    cursor.execute("SELECT SUM(amount) as total FROM expenses")
    total_result = cursor.fetchone()
    total = total_result[0] if total_result[0] else 0
    
    conn.close()
    
    category_totals = {row[0]: row[1] for row in summary}
    
    return {
        "total": total,
        "categories": category_totals
    }

@router.post("/monthly-plan")
async def set_monthly_plan(plan_data: dict, user_id: str = Depends(verify_token)):
    """Set monthly income and budget plan"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            income REAL NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(month, user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            month TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            UNIQUE(category, month, user_id)
        )
    ''')
    
    month = plan_data.get('month')
    income = plan_data.get('income')
    
    # Set income
    cursor.execute(
        "INSERT OR REPLACE INTO monthly_plans (month, income, user_id) VALUES (?, ?, ?)",
        (month, income, user_id)
    )
    
    # Set budgets
    for category, amount in plan_data.get('budgets', {}).items():
        cursor.execute(
            "INSERT OR REPLACE INTO budgets (category, amount, month, user_id) VALUES (?, ?, ?, ?)",
            (category, amount, month, user_id)
        )
    
    conn.commit()
    conn.close()
    return {"message": "Monthly plan set successfully"}

@router.get("/monthly-plan/{month}")
async def get_monthly_plan(month: str, user_id: str = Depends(verify_token)):
    """Get monthly plan (income + budgets)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get income
    cursor.execute("SELECT income FROM monthly_plans WHERE month = ? AND user_id = ?", (month, user_id))
    income_result = cursor.fetchone()
    income = income_result[0] if income_result else 0
    
    # Get budgets
    cursor.execute("SELECT category, amount FROM budgets WHERE month = ? AND user_id = ?", (month, user_id))
    budgets = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "income": income,
        "budgets": budgets,
        "total_planned": sum(budgets.values())
    }

@router.get("/budget-status/{month}")
async def get_budget_status(month: str, user_id: str = Depends(verify_token)):
    """Get budget vs actual spending status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get budgets
    cursor.execute("SELECT category, amount FROM budgets WHERE month = ? AND user_id = ?", (month, user_id))
    budgets = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get actual spending for the month
    cursor.execute("""
        SELECT category, SUM(amount) as spent
        FROM expenses 
        WHERE strftime('%Y-%m', created_at) = ? AND user_id = ?
        GROUP BY category
    """, (month, user_id))
    spending = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
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

@router.get("/expenses/analytics")
async def get_expenses_analytics(user_id: str = Depends(verify_token)):
    """Get expense analytics for dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Monthly trends
    cursor.execute("""
        SELECT strftime('%Y-%m', created_at) as month, SUM(amount) as total
        FROM expenses 
        WHERE user_id = ?
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY month DESC
        LIMIT 6
    """, (user_id,))
    monthly_trends = [{'month': row[0], 'total': row[1]} for row in cursor.fetchall()]
    
    # Category breakdown
    cursor.execute("""
        SELECT category, SUM(amount) as total, COUNT(*) as count
        FROM expenses 
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
    """, (user_id,))
    category_breakdown = [{'category': row[0], 'total': row[1], 'count': row[2]} for row in cursor.fetchall()]
    
    # Recent activity (last 7 days)
    cursor.execute("""
        SELECT DATE(created_at) as date, SUM(amount) as total
        FROM expenses 
        WHERE created_at >= date('now', '-7 days') AND user_id = ?
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """, (user_id,))
    recent_activity = [{'date': row[0], 'total': row[1]} for row in cursor.fetchall()]
    
    # Top expenses
    cursor.execute("""
        SELECT category, amount, description, created_at
        FROM expenses 
        WHERE user_id = ?
        ORDER BY amount DESC
        LIMIT 5
    """, (user_id,))
    top_expenses = [{'category': row[0], 'amount': row[1], 'description': row[2], 'date': row[3]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "monthly_trends": monthly_trends,
        "category_breakdown": category_breakdown,
        "recent_activity": recent_activity,
        "top_expenses": top_expenses
    }
