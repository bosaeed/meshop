from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User, UserCreate, UserLogin
from app.utils.database import insert_one, find_one, update_one
from passlib.context import CryptContext

router = APIRouter(prefix="/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    existing_user = await find_one("users", {"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user.password)
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]
    
    user_id = await insert_one("users", user_dict)
    return {**user_dict, "id": user_id}

@router.post("/login")
async def login_user(user: UserLogin):
    db_user = await find_one("users", {"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    return {"access_token": db_user["id"], "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = await find_one("users", {"_id": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/preferences")
async def update_preferences(preferences: list[str], current_user: User = Depends(get_current_user)):
    await update_one("users", {"_id": current_user["id"]}, {"preferences": preferences})
    return {"message": "Preferences updated successfully"}