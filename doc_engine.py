"""
doc_engine.py — Document-based Q&A engine
Replaces the old LlamaIndex + OpenAI setup with:
  1. Local keyword search over plain .txt files in the /data folder.
  2. Pollinations AI to generate a natural-language answer using the matched text.

This approach requires no API keys and works fully offline for the search step.
"""

import os
import requests
from urllib.parse import quote


DATA_FOLDER = "data"   # folder containing your .txt health documents


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT LOADING
# Load all .txt files from the data/ folder into memory at startup.
# ─────────────────────────────────────────────────────────────────────────────

def load_documents(folder: str = DATA_FOLDER) -> dict:
    """
    Read all .txt files in the data folder.

    Returns:
        A dict mapping filename → file content string.
    """
    docs = {}
    if not os.path.isdir(folder):
        print(f"[WARNING] Data folder '{folder}' not found. Document Q&A disabled.")
        return docs

    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    docs[filename] = f.read()
            except OSError as e:
                print(f"[WARNING] Could not read {filename}: {e}")

    return docs


# Load documents once at module import time
DOCUMENTS = load_documents()


# ─────────────────────────────────────────────────────────────────────────────
# KEYWORD SEARCH
# Simple relevance search: score each document by how many query words it contains.
# ─────────────────────────────────────────────────────────────────────────────

def _search_documents(query: str, top_k: int = 2) -> str:
    """
    Find the most relevant document sections for the given query.

    Args:
        query : The user's question.
        top_k : How many documents to include in context.

    Returns:
        Concatenated relevant document text, or empty string if nothing found.
    """
    if not DOCUMENTS:
        return ""

    query_words = set(query.lower().split())
    scores = {}

    for filename, content in DOCUMENTS.items():
        content_lower = content.lower()
        # Score = number of query words found in the document
        score = sum(1 for word in query_words if word in content_lower)
        if score > 0:
            scores[filename] = score

    if not scores:
        return ""

    # Sort by score, take top_k documents
    top_docs = sorted(scores, key=scores.get, reverse=True)[:top_k]

    # Return the relevant text (first 1500 characters per doc to keep prompt short)
    context_parts = []
    for doc in top_docs:
        context_parts.append(f"--- {doc} ---\n{DOCUMENTS[doc][:1500]}")

    return "\n\n".join(context_parts)


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT Q&A MAIN FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def query_documents(user_query: str, role: str = "patient") -> str:
    """
    Answer a user query using the local document library + Pollinations AI.

    Args:
        user_query : The user's question.
        role       : "patient" or "doctor" — adjusts answer depth.

    Returns:
        AI-generated answer grounded in the document content.
    """
    context = _search_documents(user_query)

    if not context:
        # No relevant documents found — fall back to general AI response
        fallback_note = "No relevant document found."
        context = fallback_note

    # Build prompt with document context
    depth = "simple, jargon-free terms" if role == "patient" else "clinical, technical detail"
    prompt = f"""You are a healthcare AI assistant. Use ONLY the following health document 
excerpts to answer the user's question in {depth}. If the documents don't contain 
relevant information, say so and suggest consulting a doctor.

DOCUMENTS:
{context}

USER QUESTION: {user_query}

Answer:"""

    encoded_prompt = quote(prompt)
    url = f"https://text.pollinations.ai/{encoded_prompt}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text.strip()

    except requests.exceptions.RequestException as e:
        return (
            "I'm unable to retrieve an answer from the document library right now. "
            f"Please try again. (Error: {str(e)[:80]})"
        )