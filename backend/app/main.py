from fastapi import FastAPI ,WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.routers import products, users, orders
from app.routers.websocket import handle_connection  # Import the WebSocket handler
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

# WebSocket endpoint
@app.websocket("/ws")
async def recommendation_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        print(data)
        output = await handle_connection(data, None)  # Call the new WebSocket handler (adjust as necessary)
        if output:
            await websocket.send_text(output)
