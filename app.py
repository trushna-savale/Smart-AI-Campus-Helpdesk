import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Smart AI Campus Helpdesk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_INSTRUCTION = """
You are the Smart AI Campus Helpdesk assistant.
Your goal is to assist students, staff, and visitors with campus inquiries, 
admissions, departments, facilities, and general help in a polite and helpful manner.
"""

class QueryRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"status": "Smart AI Campus Helpdesk API is online"}

@app.post("/chat")
def chat(request: QueryRequest):
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"error": "GROQ_API_KEY environment variable is missing."}
            
        client = Groq(api_key=api_key)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": request.message}
            ],
            model="llama-3.3-70b-versatile",
        )
        return {"response": chat_completion.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}