from fastapi import FastAPI ,WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.routers import products, users, orders
from app.routers.websocket import handle_connection  # Import the WebSocket handler
from dotenv import load_dotenv
import os
# import pyaudio
# import sounddevice as sd
# import numpy as np


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

# p = pyaudio.PyAudio()

# # Open a stream to write the audio data to the speakers
# stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
#                 channels=wf.getnchannels(),
#                 rate=wf.getframerate(),
#                 output=True)


@app.get("/")
async def root():
    return {"message": "Welcome to MeShop API"}

# WebSocket endpoint
@app.websocket("/ws")
async def recommendation_websocket(websocket: WebSocket):
    await websocket.accept()

    # buffer = bytearray()
    while True:
        # data = await websocket.receive_bytes()
        # # Process the audio data, e.g. write to speaker
        # # stream.write(data)

        # buffer.extend(data)
            
        # # Process the buffer in chunks that are multiples of int16 (2 bytes)
        # chunk_size = 2  # int16 uses 2 bytes
        # num_elements = len(buffer) // chunk_size
        # end = num_elements * chunk_size
        
        # # Convert to NumPy array and play
        # if num_elements > 0:
        #     audio_data = np.frombuffer(buffer[:end], dtype=np.int16)
        #     buffer = buffer[end:]  # Keep leftover bytes
            
        #     # Play audio using sounddevice
        #     sd.play(audio_data, samplerate=44100)
        #     sd.wait()

        data = await websocket.receive_text()
        print(data)
        output = await handle_connection(data, websocket=websocket)  # Call the new WebSocket handler (adjust as necessary)
        if output:
            await websocket.send_text(output)
