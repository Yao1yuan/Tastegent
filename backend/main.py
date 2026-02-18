from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import shutil
import uuid
from pathlib import Path
from PIL import Image
import io
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory to serve static files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Generate a unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        # Check if it's an image and compress if necessary
        if file.content_type.startswith("image/"):
            try:
                # Read image content
                content = await file.read()
                image = Image.open(io.BytesIO(content))

                # Convert to RGB if necessary (e.g. for PNGs with transparency if saving as JPEG)
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")

                # Compress and save as JPEG
                compressed_filename = f"{uuid.uuid4()}.jpg"
                compressed_path = UPLOAD_DIR / compressed_filename

                # Resize if too large (max 1920x1080)
                max_size = (1920, 1080)
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save with quality optimization
                image.save(compressed_path, "JPEG", quality=85, optimize=True)

                return {
                    "filename": compressed_filename,
                    "url": f"/uploads/{compressed_filename}",
                    "original_filename": file.filename,
                    "content_type": "image/jpeg"
                }
            except Exception as e:
                print(f"Error compressing image: {e}")
                # Fallback to saving original file if compression fails
                file.file.seek(0)

        # Save original file if not an image or compression failed
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "filename": unique_filename,
            "url": f"/uploads/{unique_filename}",
            "original_filename": file.filename,
            "content_type": file.content_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    store_id: Optional[str] = None

# Load menu data
try:
    with open("menu.json", "r") as f:
        menu_data = json.load(f)
except FileNotFoundError:
    print("Warning: menu.json not found, using empty menu")
    menu_data = []

@app.get("/")
async def root():
    return {"message": "Restaurant Agent API is running"}

@app.get("/menu")
async def get_menu():
    return menu_data

@app.post("/chat")
async def chat(request: ChatRequest):
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")

    # Construct system prompt
    menu_str = json.dumps(menu_data, indent=2)
    system_prompt = f"""You are a helpful restaurant agent.
You are helping a customer with their order.
Here is the menu:
{menu_str}

Answer questions about the menu, recommend dishes, and help the customer decide.
Be polite and concise.
"""

    if google_key:
        try:
            genai.configure(api_key=google_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            # Gemini chat history structure
            history = []

            # Add system prompt as the first part of the conversation if possible,
            # or just rely on context in the first user message.
            # Gemini's chat history is a list of Content objects.
            # Simulating system prompt by prepending to the first user message or sending it first.

            # Let's construct the history properly
            # Note: Gemini roles are 'user' and 'model'

            gemini_history = []

            # Add system prompt as context
            gemini_history.append({
                "role": "user",
                "parts": [system_prompt]
            })

            gemini_history.append({
                "role": "model",
                "parts": ["Understood. I am ready to help the customer with the menu."]
            })

            # Append conversation history
            for msg in request.messages[:-1]: # All except the last one which is the new prompt
                role = "user" if msg.role == "user" else "model"
                gemini_history.append({
                    "role": role,
                    "parts": [msg.content]
                })

            chat_session = model.start_chat(history=gemini_history)

            last_message = request.messages[-1].content
            response = chat_session.send_message(last_message)

            return {
                "role": "assistant",
                "content": response.text
            }

        except Exception as e:
            print(f"Error calling Gemini: {e}")
            import traceback
            traceback.print_exc()
            return {"role": "assistant", "content": "Sorry, I encountered an error with the AI service."}

    elif anthropic_key:
        try:
            client = Anthropic(api_key=anthropic_key)

            messages = []
            for msg in request.messages:
                if msg.role in ["user", "assistant"]:
                    messages.append({"role": msg.role, "content": msg.content})

            response = client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )

            return {
                "role": "assistant",
                "content": response.content[0].text
            }
        except Exception as e:
            print(f"Error calling Anthropic: {e}")
            import traceback
            traceback.print_exc()
            return {"role": "assistant", "content": "Sorry, I encountered an error with the AI service."}

    elif openai_key:
        try:
            client = OpenAI(api_key=openai_key)

            messages = [{"role": "system", "content": system_prompt}]
            for msg in request.messages:
                messages.append({"role": msg.role, "content": msg.content})

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )

            return {
                "role": "assistant",
                "content": response.choices[0].message.content
            }
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            import traceback
            traceback.print_exc()
            return {"role": "assistant", "content": "Sorry, I encountered an error with the AI service."}

    else:
        return {
            "role": "assistant",
            "content": "Configuration missing. Please set GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY in the backend environment."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
