"""
main.py — FastAPI application entry point
MediCare AI Healthcare Chatbot Backend

Run with:
    uvicorn main:app --reload --port 8000

Endpoints:
    GET  /              — health check
    POST /chat          — main AI chat (patient or doctor mode)
    POST /doc-chat      — document-grounded Q&A
    POST /clear-session — clear a session's conversation history
    GET  /health        — liveness probe
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import ChatRequest, DocChatRequest, ChatResponse
from chat_engine import get_response, clear_session
from crisis import contains_crisis_keywords, SAFETY_MESSAGE
from logger import log_chat
from doc_engine import query_documents

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MediCare AI — Healthcare Chatbot API",
    description="AI-powered health assistant for patients and doctors, powered by Pollinations AI.",
    version="2.0.0"
)

# Allow all origins in development.
# In production, replace "*" with your actual frontend domain, e.g.:
# allow_origins=["https://yourapp.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    """Welcome message and basic API info."""
    return {
        "message": "Welcome to MediCare AI — Healthcare Chatbot API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "chat": "POST /chat",
            "doc_chat": "POST /doc-chat",
            "clear_session": "POST /clear-session",
            "health": "GET /health"
        }
    }


@app.get("/health")
def health_check():
    """Simple liveness probe for deployment environments."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
def chat_with_ai(request: ChatRequest):
    """
    Main chat endpoint.
    - Checks for crisis keywords first (safety net).
    - Routes to Pollinations AI for normal queries.
    - Applies doctor vs. patient persona based on 'role' field.
    """
    session_id = request.session_id
    user_query = request.query.strip()
    role = request.role or "patient"

    # Validate input
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if len(user_query) > 2000:
        raise HTTPException(status_code=400, detail="Query is too long (max 2000 characters).")

    # ── Crisis detection (highest priority) ──────────────────────────────────
    if contains_crisis_keywords(user_query):
        log_chat(session_id, user_query, SAFETY_MESSAGE, is_crisis=True, role=role)
        return ChatResponse(
            response=SAFETY_MESSAGE,
            is_crisis=True,
            source="crisis"
        )

    # ── Normal AI response ───────────────────────────────────────────────────
    ai_reply = get_response(session_id, user_query, role=role)
    log_chat(session_id, user_query, ai_reply, is_crisis=False, role=role)

    return ChatResponse(
        response=ai_reply,
        is_crisis=False,
        source="ai"
    )


@app.post("/doc-chat", response_model=ChatResponse)
def chat_with_documents(request: DocChatRequest):
    """
    Document Q&A endpoint.
    Answers questions using the health documents in the /data folder.
    BUG FIX: Renamed from '/doc.chat' — dots in URL paths cause routing issues.
    """
    user_query = request.query.strip()
    role = request.role or "patient"

    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    answer = query_documents(user_query, role=role)

    return ChatResponse(
        response=answer,
        is_crisis=False,
        source="document"
    )


@app.post("/clear-session")
def clear_chat_session(request: ChatRequest):
    """
    Clear the conversation history for a session.
    Call this when the user clicks 'New Chat'.
    """
    clear_session(request.session_id)
    return {"message": f"Session '{request.session_id}' cleared successfully."}