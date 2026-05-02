"""
models.py — Pydantic request/response schemas
Defines the shape of data sent to and received from the API endpoints.
"""

from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    """
    Payload for the /chat endpoint.
    
    Fields:
        session_id : Unique ID per browser session (generated on frontend).
        query      : The user's message text.
        role       : "patient" or "doctor" — controls the AI's tone and depth.
    """
    session_id: str
    query: str
    role: Optional[str] = "patient"   # default to patient if not provided


class DocChatRequest(BaseModel):
    """
    Payload for the /doc-chat endpoint (document Q&A).
    
    Fields:
        query : The user's question about the health document library.
        role  : Controls how technical the answer should be.
    """
    query: str
    role: Optional[str] = "patient"


class ChatResponse(BaseModel):
    """
    Standard response wrapper returned by all chat endpoints.
    
    Fields:
        response   : The AI's reply text.
        is_crisis  : True when a crisis keyword was detected.
        source     : 'ai' | 'crisis' | 'document' — where the answer came from.
    """
    response: str
    is_crisis: bool = False
    source: str = "ai"