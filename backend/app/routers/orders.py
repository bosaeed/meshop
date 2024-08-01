from fastapi import APIRouter, HTTPException, Depends
from app.models.order import Order, OrderCreate
from app.utils.database import insert_one, find_many
from app.routers.users import get_current_user
from app.models.user import User

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=Order)
async def create_order(order: OrderCreate, current_user: User = Depends(get_current_user)):
    order_dict = order.dict()
    order_dict["user_id"] = current_user["id"]
    order_id = await insert_one("orders", order_dict)
    return {**order_dict, "id": order_id}

@router.get("/", response_model=list[Order])
async def get_user_orders(current_user: User = Depends(get_current_user)):
    return await find_many("orders", {"user_id": current_user["id"]})