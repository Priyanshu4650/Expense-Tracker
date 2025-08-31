from fastapi import APIRouter, Depends
from services.budget_service import set_monthly_plan, get_monthly_plan, get_budget_status
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/budget", tags=["Budget"])

@router.post("/monthly-plan")
async def set_monthly_plan_route(plan_data: dict, user_id: str = Depends(get_current_user)):
    return set_monthly_plan(
        plan_data.get('month'), 
        plan_data.get('income'), 
        plan_data.get('budgets', {}), 
        user_id
    )

@router.get("/monthly-plan/{month}")
async def get_monthly_plan_route(month: str, user_id: str = Depends(get_current_user)):
    return get_monthly_plan(month, user_id)

@router.get("/budget-status/{month}")
async def get_budget_status_route(month: str, user_id: str = Depends(get_current_user)):
    return get_budget_status(month, user_id)