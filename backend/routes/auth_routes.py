from fastapi import APIRouter
from models.user import UserCreate, UserLogin
from services.auth_service import register_user, login_user

router = APIRouter(tags=["Authentication"])

@router.post("/register")
async def register(user: UserCreate):
    return register_user(user.username, user.password)

@router.post("/login")
async def login(user: UserLogin):
    return login_user(user.username, user.password)