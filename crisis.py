"""
crisis.py — Crisis detection module
Scans user messages for emergency/crisis keywords and returns a
pre-written safety message with helpline numbers.

This is a critical safety feature — always checked BEFORE sending
the message to the AI model.
"""

from typing import List

# ─────────────────────────────────────────────────────────────────────────────
# CRISIS KEYWORDS
# Any message containing one of these triggers the SAFETY_MESSAGE response.
# ─────────────────────────────────────────────────────────────────────────────

CRISIS_KEYWORDS: List[str] = [
    # Suicidal ideation
    "suicidal", "suicide", "want to die", "wanna die", "end my life",
    "kill myself", "take my life", "not worth living", "better off dead",
    "better off without me", "no reason to live", "don't want to be alive",
    "dont want to be alive", "wish i was dead", "ready to die", "planning to die",

    # Self-harm
    "self harm", "self-harm", "cutting myself", "hurt myself",
    "harming myself", "burn myself", "starving myself",

    # Hopelessness
    "no hope", "hopeless", "nothing to live for", "can't go on",
    "cannot go on", "can't take it anymore", "cannot take it anymore",
    "i give up", "i quit life", "tired of living", "done with life",
    "done with everything", "no point in living", "no point anymore",

    # Crisis / Emergency
    "in danger", "not safe", "feeling unsafe", "going to hurt",
    "going to harm", "overdose", "took pills", "swallowed pills",
    "drinking bleach", "jumped off", "jumping off",

    # Goodbye signals
    "goodbye forever", "final goodbye", "last message",
    "nobody will miss me", "no one will miss me",
    "world is better without me", "leaving this world",
    "this is the end", "won't be here anymore",

    # Abuse
    "being abused", "someone is hurting me", "he hits me", "she hits me",
    "physically abused", "sexually abused", "domestic violence", "trapped at home",
]


# ─────────────────────────────────────────────────────────────────────────────
# SAFETY MESSAGE
# Shown immediately when a crisis keyword is detected.
# ─────────────────────────────────────────────────────────────────────────────

SAFETY_MESSAGE = (
    "I'm really sorry you're feeling this way. You're not alone, and your life matters.\n\n"
    "Please reach out to a professional who can truly help you right now:\n\n"
    "🇮🇳 India Crisis Helplines:\n"
    "  • iCall                   : 9152987821\n"
    "  • Vandrevala Foundation    : 1860-2662-345 (24/7)\n"
    "  • AASRA                   : 9820466627\n"
    "  • Snehi                   : 044-24640050\n\n"
    "International:\n"
    "  • Find a helpline          : https://findahelpline.com\n"
    "  • Crisis Text Line         : Text HOME to 741741\n\n"
    "🏥 If you are in immediate danger, please call:\n"
    "  • Emergency (India)        : 112\n\n"
    "I'm here to listen, but please talk to someone who can give you "
    "the real support you deserve. 💙"
)


def contains_crisis_keywords(text: str) -> bool:
    """
    Return True if any crisis keyword is found in the text.

    Args:
        text : The user's message (case-insensitive check).
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in CRISIS_KEYWORDS)