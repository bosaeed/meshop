# app/routers/telegram.py

import json
from telegram import Bot, Update ,InputMediaPhoto
from telegram.ext import CommandHandler, MessageHandler, filters, Application
from app.services.recommendation_service import process_user_input
import os
from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(JSONEncoder, self).default(obj)

class TelegramSender():
    def __init__(self,update) -> None:
        self.update = update
        self.last_wait = None

    async def send_text(self,messageData ,isText = False):
        print("send telegram text")
        if(isText):
            msg = messageData
        else:
            msg = json.loads(messageData).get("message"," ")
        if(self.last_wait):
            await self.last_wait.edit_text(msg)
            self.last_wait = None
        elif(msg == "wait..."):
            print("send wait text")
            self.last_wait = await self.update.message.reply_text(msg)

        else:
            print("send reply_text")
            await self.update.message.reply_text(msg)

    async def reply_media_group(self,media):
        print("send telegram media")
        await self.update.message.reply_media_group(media=media)

last_products = []

async def start(update: Update, context):
    print("Received start command")
    print(update.message)
    await update.message.reply_text('Welcome to MeShop! How can I assist you today?')

async def handle_message(update: Update, context):
    print("Received Message")
    print(update.message)
    print("effective sender id: ",update.effective_sender.id)
    user_id = update.effective_sender.id
    
    user_input = update.message.text
    # tsender = TelegramSender(update)
    await update.message.reply_text("...")

    tsender = None
    prediction = process_user_input(user_input,tsender,user_id=user_id)
    
    output = {}
    
    # if hasattr(prediction, 'error'):
    #     output['error'] = prediction.error
    if prediction.action == 'recommend':
        media_group = []
        for i, product in enumerate(prediction.products):
            caption = f"{i+1}. {product['name']} - {product['sale_price']}"
            if(len(product["images"]) > 0):
                # media_group.append(InputMediaPhoto(media=product['images'][0], caption=caption,show_caption_above_media=True))
                await update.message.reply_photo(photo=product['images'][0], caption=caption,show_caption_above_media=True)
            else:
                await update.message.reply_text(caption)
        if media_group:
            await update.message.reply_media_group(media=media_group)
        elif (len(prediction.products) < 1):
            await update.message.reply_text("Sorry, I couldn't find any products to recommend.")



    elif prediction.action == 'add_to_cart':
        cart_items = "\n".join([f"{item['name']} (x{item['quantity']}) - {item['sale_price']}" for item in prediction.current_cart])
        await update.message.reply_text(f"Added to cart:\n{cart_items}")




    elif prediction.action == 'more_info':
        await update.message.reply_text(f"💬: {prediction.summery}")

    await update.message.reply_text(prediction.feedback)

    return json.dumps(output, cls=JSONEncoder)

async def handle_telegram_update(data , user_id=" "):
    # Create the Application
    application = Application.builder().token(os.getenv("TELEGRAM_API_TOKEN")).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Process the update
    await application.initialize()
    await application.process_update(Update.de_json(data, application.bot))
    await application.shutdown()

