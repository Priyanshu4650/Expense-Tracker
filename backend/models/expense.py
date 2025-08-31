from pydantic import BaseModel

class ExpenseCreate(BaseModel):
    category: str
    amount: float
    description: str = ""
    payment_date: str = ""

class Expense(BaseModel):
    id: str
    category: str
    amount: float
    description: str
    payment_date: str
    created_at: str