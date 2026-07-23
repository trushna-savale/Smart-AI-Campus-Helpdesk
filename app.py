import os
import re
import csv
import io
import sqlite3
import random
from datetime import datetime
from fastapi import FastAPI, Response
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

DB_FILE = "helpdesk.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Removed UNIQUE constraint from ticket_id to prevent IntegrityErrors
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT,
            timestamp TEXT NOT NULL,
            student_name TEXT DEFAULT 'Anonymous',
            prn TEXT DEFAULT 'N/A',
            section TEXT DEFAULT 'N/A',
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            category TEXT DEFAULT 'General',
            image_data TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def extract_ticket_info(bot_response: str):
    ticket_match = re.search(r'CMP-\d+', bot_response)
    if ticket_match:
        ticket_id = ticket_match.group(0)
    else:
        ticket_id = f"CMP-{random.randint(100000, 999999)}"
    
    category = "General"
    bot_lower = bot_response.lower()
    if "electrical" in bot_lower or "fan" in bot_lower or "light" in bot_lower:
        category = "Electrical"
    elif "it" in bot_lower or "wifi" in bot_lower or "internet" in bot_lower:
        category = "IT Support"
    elif "maintenance" in bot_lower or "cleaning" in bot_lower or "projector" in bot_lower:
        category = "Maintenance"
        
    return ticket_id, category

def log_to_db(student_name: str, prn: str, section: str, user_message: str, bot_response: str, image_data: str = None):
    try:
        ticket_id, category = extract_ticket_info(bot_response)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO chat_logs 
               (ticket_id, timestamp, student_name, prn, section, user_message, bot_response, status, category, image_data) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ticket_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), student_name, prn, section, user_message, bot_response, 'Open', category, image_data)
        )
        conn.commit()
        conn.close()
        return ticket_id
    except Exception as e:
        print(f"Database logging error (handled): {e}")
        ticket_match = re.search(r'CMP-\d+', bot_response)
        return ticket_match.group(0) if ticket_match else "CMP-100000"

SYSTEM_INSTRUCTION = """
You are the Smart AI Campus Helpdesk assistant.
Your job is to help students register campus complaints professionally.

For EVERY complaint reported, generate an official support ticket in this exact format:


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


Be clear, professional, and reassuring.
"""

class QueryRequest(BaseModel):
    message: str
    student_name: str = "Anonymous"
    prn: str = "N/A"
    section: str = "N/A"
    image_data: str = None

class StatusUpdateRequest(BaseModel):
    ticket_id: str
    status: str

@app.get("/")
def home():
    return {"status": "Smart AI Campus Helpdesk API is online"}

@app.post("/chat")
def chat(request: QueryRequest):
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"response": "GROQ_API_KEY environment variable is missing on server.", "ticket_id": None}
            
        client = Groq(api_key=api_key)
        
        prompt_content = f"Student Info: Name={request.student_name}, PRN={request.prn}, Section={request.section}. Issue: {request.message}"
        if request.image_data:
            prompt_content += " [Photo proof attached by student]."

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt_content}
            ],
            model="llama-3.3-70b-versatile",
        )
        
        bot_reply = chat_completion.choices[0].message.content
        ticket_id = log_to_db(request.student_name, request.prn, request.section, request.message, bot_reply, request.image_data)
        
        return {"response": bot_reply, "ticket_id": ticket_id}
    except Exception as e:
        print(f"Chat execution error: {e}")
        return {"response": f"Server processing error: {str(e)}", "ticket_id": None}

@app.get("/ticket/{query}")
def get_ticket(query: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_logs WHERE ticket_id = ? OR prn = ? ORDER BY id DESC", (query, query))
    rows = cursor.fetchall()
    conn.close()
    if rows:
        return {"tickets": [dict(r) for r in rows]}
    return {"error": "No records found for given Ticket ID or PRN"}

@app.get("/admin/logs")
def get_all_logs():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return {"total_logs": len(rows), "data": [dict(row) for row in rows]}

@app.post("/admin/update-status")
def update_status(req: StatusUpdateRequest):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE chat_logs SET status = ? WHERE ticket_id = ?", (req.status, req.ticket_id))
    conn.commit()
    conn.close()
    return {"status": "success", "ticket_id": req.ticket_id, "new_status": req.status}

@app.get("/admin/export-csv")
def export_csv():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id, timestamp, student_name, prn, section, category, status, user_message FROM chat_logs")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Ticket ID", "Timestamp", "Name", "PRN", "Section", "Category", "Status", "User Message"])
    writer.writerows(rows)

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=campus_tickets.csv"
    return response

@app.get("/admin/analytics")
def get_analytics():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM chat_logs")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE status = 'Open'")
    open_tickets = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE status = 'Resolved'")
    resolved_tickets = cursor.fetchone()[0]
    
    cursor.execute("SELECT category, COUNT(*) FROM chat_logs GROUP BY category ORDER BY COUNT(*) DESC LIMIT 1")
    top_cat = cursor.fetchone()
    top_category = top_cat[0] if top_cat else "None"
    
    conn.close()
    return {
        "total_tickets": total,
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
        "top_category": top_category
    }