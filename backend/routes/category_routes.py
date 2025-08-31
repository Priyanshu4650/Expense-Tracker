from fastapi import APIRouter, Depends
from models.category import CategoryCreate
from services.category_service import create_category, get_categories
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("", response_model=dict)
async def create_category_route(category: CategoryCreate, user_id: str = Depends(get_current_user)):
    return create_category(category.name)

@router.get("")
async def get_categories_route(user_id: str = Depends(get_current_user)):
    return get_categories()