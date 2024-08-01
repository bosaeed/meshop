from pydantic import BaseModel, EmailStr ,Field
from typing import List, Optional
from bson import ObjectId
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class User(BaseModel):
    id: Optional[PyObjectId]  = Field( alias="_id")
    email: EmailStr
    hashed_password: str
    preferences: Optional[List[str]] = []
    interaction_history: Optional[List[dict]] = []

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str