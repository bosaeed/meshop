from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import products, users, orders
from dotenv import load_dotenv
import os

load_dotenv()



app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router)
app.include_router(users.router)
app.include_router(orders.router)

@app.get("/")
async def root():
    return {"message": "Welcome to MeShop API"}