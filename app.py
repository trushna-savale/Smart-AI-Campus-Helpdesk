import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Smart AI Campus Helpdesk API")

# Allow CORS for public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------
DB_FILE = "helpdesk.db"

def init_db():
    """Create the logs table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Initialize DB when app starts
init_db()

def log_to_db(user_message: str, bot_response: str):
    """Save a user query and bot response to SQLite."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_logs (timestamp, user_message, bot_response) VALUES (?, ?, ?)",
            (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user_message, bot_response)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database logging error: {e}")

# ---------------------------------------------------------
# PROMPT & ROUTING
# ---------------------------------------------------------
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
        
        bot_reply = chat_completion.choices[0].message.content
        
        # Save interaction to central database
        log_to_db(request.message, bot_reply)
        
        return {"response": bot_reply}
    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------
# ADMIN ENDPOINT: VIEW ALL USER DATA
# ---------------------------------------------------------
@app.get("/admin/logs")
def get_all_logs():
    """Admin-only endpoint to view all logged interactions."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_logs ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        
        logs = [dict(row) for row in rows]
        return {"total_logs": len(logs), "data": logs}
    except Exception as e:
        return {"error": str(e)}