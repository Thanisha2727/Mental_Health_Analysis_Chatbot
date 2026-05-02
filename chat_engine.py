"""
chat_engine.py — Core AI engine powered by Pollinations AI
Replaces the old OpenAI/LangChain setup with direct Pollinations API calls.
Maintains per-session conversation history for multi-turn memory.

Pollinations API docs: https://text.pollinations.ai
"""

import requests
from urllib.parse import quote

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPTS  (one per role)
# ─────────────────────────────────────────────────────────────────────────────

PATIENT_SYSTEM_PROMPT = """You are MediCare AI, a compassionate and knowledgeable 
AI health assistant designed to support patients. Your role is to:

1. Provide clear, empathetic, and easy-to-understand health information.
2. Help users understand symptoms, general wellness tips, and when to seek care.
3. Offer emotional support for mental health concerns with warmth and care.
4. ALWAYS recommend consulting a licensed doctor for diagnosis or treatment.
5. Never prescribe medications or make definitive medical diagnoses.
6. Keep responses concise, friendly, and jargon-free for general audiences.
7. If a user seems distressed, acknowledge their feelings first before giving info.

Remember: You are a supportive guide, not a replacement for professional medical care.
Always end serious medical queries with a reminder to consult a healthcare professional."""


DOCTOR_SYSTEM_PROMPT = """You are MediCare AI, a clinical decision-support assistant 
designed for healthcare professionals. Your role is to:

1. Provide detailed, evidence-based clinical information using proper medical terminology.
2. Assist with differential diagnoses, treatment protocols, and drug interactions.
3. Reference relevant medical guidelines (WHO, CDC, NICE, etc.) when applicable.
4. Support clinical reasoning with structured, systematic responses.
5. Discuss pharmacology, dosing ranges, contraindications, and side-effect profiles.
6. Assist with interpreting lab values, imaging findings, and diagnostic criteria.
7. Always note when information should be cross-checked with the latest guidelines.

Remember: This tool supports, not replaces, clinical judgment. Always verify 
critical information with primary sources and institutional protocols."""


# ─────────────────────────────────────────────────────────────────────────────
# IN-MEMORY SESSION STORE
# Stores conversation history per session_id so the AI has context memory.
# Format: { session_id: [ {"role": "user"|"assistant", "content": "..."}, ... ] }
# ─────────────────────────────────────────────────────────────────────────────

session_history: dict = {}

# Maximum number of turns to keep in memory (to avoid huge prompts)
MAX_HISTORY_TURNS = 10


def _get_system_prompt(role: str) -> str:
    """Return the correct system prompt based on the user's role."""
    if role.lower() == "doctor":
        return DOCTOR_SYSTEM_PROMPT
    return PATIENT_SYSTEM_PROMPT


def _build_prompt_text(session_id: str, user_query: str, role: str) -> str:
    """
    Build a single text prompt that includes conversation history.
    Pollinations GET endpoint takes a plain-text prompt, so we format
    the whole conversation as a readable context block.
    """
    system = _get_system_prompt(role)
    history = session_history.get(session_id, [])

    # Build conversation block
    convo_lines = [f"SYSTEM: {system}", ""]
    for turn in history[-MAX_HISTORY_TURNS:]:
        speaker = "User" if turn["role"] == "user" else "Assistant"
        convo_lines.append(f"{speaker}: {turn['content']}")

    convo_lines.append(f"User: {user_query}")
    convo_lines.append("Assistant:")

    return "\n".join(convo_lines)


def get_response(session_id: str, user_query: str, role: str = "patient") -> str:
    """
    Send the user's query to Pollinations AI and return the AI's reply.

    Args:
        session_id : Unique session identifier (from frontend).
        user_query : The message the user typed.
        role       : "patient" or "doctor" — controls system prompt.

    Returns:
        AI response as a string, or an error message on failure.
    """

    # 1. Build the full prompt with history context
    full_prompt = _build_prompt_text(session_id, user_query, role)

    # 2. URL-encode the prompt (required for GET request)
    encoded_prompt = quote(full_prompt)

    # 3. Call the Pollinations AI API
    url = f"https://text.pollinations.ai/{encoded_prompt}"

    try:
        response = requests.get(
            url,
            timeout=30,          # wait up to 30 seconds for a response
            headers={
                "User-Agent": "MediCare-Chatbot/1.0"
            }
        )
        response.raise_for_status()  # raise error for 4xx / 5xx status codes
        ai_reply = response.text.strip()

    except requests.exceptions.Timeout:
        ai_reply = (
            "I'm sorry, the AI service is taking too long to respond right now. "
            "Please try again in a moment."
        )
    except requests.exceptions.ConnectionError:
        ai_reply = (
            "I'm having trouble connecting to the AI service. "
            "Please check your internet connection and try again."
        )
    except requests.exceptions.RequestException as e:
        ai_reply = (
            f"An error occurred while contacting the AI service. "
            f"Please try again later. (Error: {str(e)[:100]})"
        )

    # 4. Save this turn to session history
    if session_id not in session_history:
        session_history[session_id] = []

    session_history[session_id].append({"role": "user", "content": user_query})
    session_history[session_id].append({"role": "assistant", "content": ai_reply})

    # Trim history if it grows too large
    if len(session_history[session_id]) > MAX_HISTORY_TURNS * 2:
        session_history[session_id] = session_history[session_id][-(MAX_HISTORY_TURNS * 2):]

    return ai_reply


def clear_session(session_id: str) -> None:
    """Clear the conversation history for a given session."""
    if session_id in session_history:
        del session_history[session_id]