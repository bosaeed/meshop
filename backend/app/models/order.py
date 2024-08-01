from pydantic import BaseModel ,Field 
from typing import List ,Optional
from datetime import datetime
from bson import ObjectId
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class OrderItem(BaseModel):
    product_id: str
    quantity: int

class Order(BaseModel):
    id: Optional[PyObjectId]  = Field( alias="_id")
    user_id: str
    items: List[OrderItem]
    total_amount: float
    created_at: datetime

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItem]