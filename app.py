import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

# Initialize the FastAPI app variable
app = FastAPI(title="Smart AI Campus Helpdesk API")

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multi-line string properly enclosed with triple quotes
SYSTEM_INSTRUCTION = """
You are an AI Smart Campus Helpdesk Assistant.
Your job is to help students register campus complaints professionally.

REQUIRED INFORMATION TO REGISTER:
1. Problem description (e.g., fan not working, AC broken, projector light flickering)
2. Location/Classroom/Lab (e.g., classroom 432, computer lab 3)

Conversation History so far:
{history}

Current Student Message:
{input}

INSTRUCTIONS:
1. Carefully check the "Conversation History so far" to see what details the user has ALREADY provided in previous turns.
2. IF location is missing: Ask ONLY for the location.
3. IF problem description is missing: Ask ONLY for the problem description.
4. IF BOTH location and problem description are provided across the conversation: Immediately output the complete SMART CAMPUS HELPDESK REPORT below.

--------------------------------------------------
SMART CAMPUS HELPDESK REPORT

Ticket ID: CMP-[Generate 6 random digits]
Complaint:

Category:

Priority:
(Low / Medium / High / Critical)

Assigned Department:

Assigned Engineer:
Generate a realistic support engineer name.

Current Status:
Open

Estimated Resolution Time:

Immediate Actions:
- Action 1
- Action 2
- Action 3

Possible Root Cause:

AI Recommendations:
1.
2.
3.

Email Draft:

Subject: Complaint Registered Successfully

Dear Student,

Your complaint has been successfully registered.

Ticket ID:

Assigned Department:

Priority:

Estimated Resolution Time:

Our support team will resolve the issue as soon as possible.

Regards,
Smart Campus Helpdesk Team

--------------------------------------------------

Always keep responses polite, concise, and structured.
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
