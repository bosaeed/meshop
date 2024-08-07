import asyncio
from fastapi import FastAPI ,WebSocket ,Request
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.routers import products, users, orders
from app.routers.websocket import handle_connection  # Import the WebSocket handler
from app.routers.telegram import handle_telegram_update
from dotenv import load_dotenv
import os
import nest_asyncio
nest_asyncio.apply()


load_dotenv()
# Initialize Telegram bot webhook on startup
async def on_startup():
    from telegram import Bot
    print("Starting bot...")
    bot = Bot(token=os.getenv("TELEGRAM_API_TOKEN"))
    webhook_url = f"{os.getenv('HOST_URL')}/telegram/{os.getenv('TELEGRAM_WEBHOOK_PATH')}"
    await bot.setWebhook(webhook_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ background task starts at startup """
    asyncio.create_task(on_startup())
    yield

app = FastAPI(lifespan=lifespan)
# app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*",os.getenv("FRONTEND_URL")],  # Add your frontend URL
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
@app.websocket("/ws/{user_id}")
async def recommendation_websocket(websocket: WebSocket , user_id):
    print(user_id)
    # print(request.args.get('user'))
    # url.parse(websocket.url, true).query

    try:
        await websocket.accept()

        # buffer = bytearray()
        while True:


            data = await websocket.receive_text()
            print(data)
            output = await handle_connection(data, websocket=websocket ,user_id=user_id)  # Call the new WebSocket handler (adjust as necessary)
            if output:
                await websocket.send_text(output)
    except Exception as e:
        print(f"WebSocket error: {type(e).__name__}:{e}")

@app.post(f"/telegram/{os.getenv('TELEGRAM_WEBHOOK_PATH')}")
async def telegram_webhook(update: Request):
    user_id =" "
    print("Received Telegram update:")
    data = await update.json()
    print(data)
    await handle_telegram_update(data,user_id=user_id)  # Call the Telegram update handler (adjust as necessary)

