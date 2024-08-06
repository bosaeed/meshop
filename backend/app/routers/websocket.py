import json
from app.services.recommendation_service import process_user_input
# from app.services.outline_recommendation import process_user_input
# from app.services.langchain_recommendation import process_user_input
from bson import ObjectId 

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(JSONEncoder, self).default(obj)


async def handle_connection(message, websocket=None,user_id=" "):
    """Handles incoming messages from a WebSocket connection."""
    # async for message in websocket:
    data = json.loads(message)
    user_input = data.get('user_input', '')
    print(user_input)
    if user_input:
        # prediction = await process_user_input(user_input, last_products )
        prediction = process_user_input(user_input ,websocket=websocket,user_id=user_id)
        
        output = {}
        if hasattr(prediction, 'error'):
            output['error'] = prediction.error
        elif prediction.action == 'recommend':
            output['products'] = prediction.products
            output['action'] = prediction.action
        elif prediction.action == 'add_to_cart':
            output['cart_items'] = prediction.cart_items
            output['action'] = prediction.action
        elif prediction.action == 'more_info':
            output['additional_info'] = prediction.additional_info
            output['action'] = prediction.action

        return json.dumps(output , cls=JSONEncoder)
