import json
# from app.services.recommendation_service import get_recommendations

async def handle_connection(message, _):
    """Handles incoming messages from a WebSocket connection."""
    # async for message in websocket:
    data = json.loads(message)
    user_input = data.get('user_input', '')
    print(user_input)
    # if user_input:
    #     recommendations = await get_recommendations(user_input, [])
    #     await websocket.send(json.dumps(recommendations))
