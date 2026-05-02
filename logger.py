"""
logger.py — Chat logging utility
Writes every conversation turn to chat_log.csv for audit and analysis.

BUG FIXED: Original code used datetime.row() which doesn't exist.
           Corrected to datetime.now().
"""

import os
import csv
from datetime import datetime


LOG_FILE = "chat_log.csv"

# CSV column headers
HEADERS = ["timestamp", "session_id", "role", "query", "response", "crisis_flag"]


def log_chat(
    session_id: str,
    query: str,
    response: str,
    is_crisis: bool,
    role: str = "patient"
) -> None:
    """
    Append a chat turn to the CSV log file.

    Args:
        session_id : Unique session ID.
        query      : The user's message.
        response   : The AI's reply.
        is_crisis  : True if a crisis keyword was detected.
        role       : "patient" or "doctor".
    """
    try:
        file_exists = os.path.isfile(LOG_FILE)

        with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write header row only for a new file
            if not file_exists:
                writer.writerow(HEADERS)

            # BUG FIX: was datetime.row() — corrected to datetime.now()
            writer.writerow([
                datetime.now().isoformat(),   # ← FIXED
                session_id,
                role,
                query,
                response,
                str(is_crisis)
            ])

    except OSError as e:
        # Don't crash the app if logging fails — just print a warning
        print(f"[WARNING] Could not write to log file: {e}")