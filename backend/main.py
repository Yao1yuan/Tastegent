from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI

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

    # Construct system prompt
    menu_str = json.dumps(menu_data, indent=2)
    system_prompt = f"""You are a helpful restaurant agent.
You are helping a customer with their order.
Here is the menu:
{menu_str}

Answer questions about the menu, recommend dishes, and help the customer decide.
Be polite and concise.
"""

    if anthropic_key:
        try:
            client = Anthropic(api_key=anthropic_key)

            # Convert messages for Anthropic
            # Anthropic expects 'user' and 'assistant' roles
            # System prompt is separate parameter

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
            print(f"Error calling Anthropic: {{e}}")
            # In production, log the error and return a generic message
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
            print(f"Error calling OpenAI: {{e}}")
            import traceback
            traceback.print_exc()
            return {"role": "assistant", "content": "Sorry, I encountered an error with the AI service."}

    else:
        return {
            "role": "assistant",
            "content": "Configuration missing. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in the backend environment."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
