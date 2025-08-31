import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from database import get_database
from bson import ObjectId

SECRET_KEY = "expense_tracker_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

db = get_database()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def register_user(username: str, password: str):
    # Check if user exists
    if db.users.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    user_doc = {
        "username": username,
        "password_hash": password_hash,
        "created_at": datetime.now()
    }
    
    db.users.insert_one(user_doc)
    return {"message": "User created successfully"}

def login_user(username: str, password: str):
    user = db.users.find_one({"username": username})
    
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user['_id'])})
    return {"access_token": access_token, "token_type": "bearer"}