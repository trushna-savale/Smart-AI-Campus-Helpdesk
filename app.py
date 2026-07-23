import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI(title="Smart AI Campus Helpdesk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini AI
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

SYSTEM_INSTRUCTION = """
You are the Smart AI Campus Helpdesk assistant.
Your goal is to assist students, staff, and visitors with campus inquiries, 
admissions, departments, facilities, and general help in a polite and helpful manner.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

class QueryRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"status": "Smart AI Campus Helpdesk API is online"}

@app.post("/chat")
def chat(request: QueryRequest):
    try:
        response = model.generate_content(request.message)
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}