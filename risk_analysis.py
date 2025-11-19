"""
AI Solutions Engineer Interview – Simple Risk Scoring Script
Author: Tinomutendayi Muzondidya
Time spent: 1 hr 45 minutes

This script:
- Loads WhatsApp-style conversations
- Extracts user messages
- Computes risk scores for HIV acquisition and mental health disorders
- Generates South African NDoH-aligned recommendations
- Produces a CSV output for further analysis
"""

import re
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict


# ============================================================
# Data structures
# ============================================================

@dataclass
class ConversationRiskResult:
    conversation_id: int
    hiv_risk_score: float
    hiv_risk_level: str
    mental_health_risk_score: float
    mental_health_risk_level: str
    hiv_recommendation: str
    mental_health_recommendation: str


# ============================================================
# Load and parse conversations
# ============================================================

def load_conversations(path: str) -> List[str]:
    """Load conversations from a TXT file and split by separator."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    return [c.strip() for c in raw.split("========== Conversation ==========") if c.strip()]


def extract_user_text(conversation: str) -> str:
    """Extract user-only messages based on 'User:' patterns."""
    user_lines = []
    for line in conversation.splitlines():
        line = line.strip()
        if "] User:" in line:
            msg = line.split("] User:", 1)[1].strip()
            user_lines.append(msg)
        elif "User:" in line:
            msg = line.split("User:", 1)[1].strip()
            user_lines.append(msg)
    return " ".join(user_lines)


# ============================================================
# Keyword dictionaries
# ============================================================

HIV_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "unprotected_sex": {
        "weight": 0.45,
        "patterns": [
            r"without a condom",
            r"no condom",
            r"didn.?t use (a )?condom",
            r"condom broke",
            r"condom slipped",
        ],
    },
    "sti_symptoms": {
        "weight": 0.25,
        "patterns": [
            r"genital (sore|sores|ulcer|ulcers|blister|blisters)",
            r"burn(s|ing)? when (i )?pee",
            r"penile discharge",
            r"vaginal discharge",
            r"smelly discharge",
        ],
    },
    "multiple_partners": {
        "weight": 0.15,
        "patterns": [
            r"multiple partners?",
            r"more than one (guy|girl|partner)",
            r"one.?night stand",
            r"hook.?up",
            r"cheated",
            r"affair",
            r"sex worker",
        ],
    },
    "partner_hiv_positive_or_unknown": {
        "weight": 0.25,
        "patterns": [
            r"partner.*(hiv\+|hiv positive)",
            r"on (arvs|art)",
            r"don.?t know.*partner.?s? status",
        ],
    },
}

MH_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "depression": {
        "weight": 0.25,
        "patterns": [
            r"(i feel|feeling) (sad|down|empty|numb)",
            r"lost interest",
            r"no energy",
            r"tired of life",
            r"worthless",
        ],
    },
    "anxiety": {
        "weight": 0.2,
        "patterns": [
            r"anxious",
            r"anxiety",
            r"panic attack",
            r"heart.*racing",
        ],
    },
    "suicidality_or_self_harm": {
        "weight": 0.6,
        "patterns": [
            r"kill myself",
            r"end it all",
            r"don.?t want to live",
            r"rather be dead",
            r"suicide",
        ],
    },
    "substance_use": {
        "weight": 0.15,
        "patterns": [
            r"drinking a lot",
            r"using (weed|dagga|marijuana|drugs)",
        ],
    },
}


# ============================================================
# Scoring functions
# ============================================================

def _keyword_score(text: str, keyword_dict: Dict[str, Dict[str, List[str]]]) -> float:
    score = 0.0
    text = text.lower()

    for _, cfg in keyword_dict.items():
        if any(re.search(pat, text) for pat in cfg["patterns"]):
            score += cfg["weight"]

    return min(score, 1.0)


def compute_hiv_risk(text: str) -> float:
    return _keyword_score(text, HIV_KEYWORDS)


def compute_mental_health_risk(text: str) -> float:
    return _keyword_score(text, MH_KEYWORDS)


def risk_level(score: float) -> str:
    if score < 0.3:
        return "low"
    elif score < 0.6:
        return "moderate"
    return "high"


# ============================================================
# Recommendations
# ============================================================

def generate_hiv_recommendation(score: float) -> str:
    level = risk_level(score)

    if level == "low":
        return (
            "HIV risk low. Recommend routine HIV testing, consistent condom use, "
            "and STI prevention."
        )

    if level == "moderate":
        return (
            "Moderate HIV risk. Recommend prompt HIV testing, STI screening, and "
            "assessment for PEP if exposure was within 72 hours."
        )

    return (
        "High HIV risk. Immediate clinical assessment advised. Evaluate for PEP, "
        "STI screening, pregnancy screening if applicable, and urgent HIV testing."
    )


def generate_mental_health_recommendation(score: float) -> str:
    level = risk_level(score)

    if level == "low":
        return (
            "Low mental health risk. Provide psychoeducation, stress management, "
            "and routine monitoring."
        )

    if level == "moderate":
        return (
            "Moderate mental health risk. Recommend clinic-based mental health "
            "assessment and counselling support."
        )

    return (
        "High mental health risk. Urgent same-day mental health assessment advised, "
        "including screening for suicidality or self-harm."
    )


# ============================================================
# Conversation analysis function
# ============================================================

def analyse_conversation(conversation_id: int, conversation_text: str) -> ConversationRiskResult:
    user_text = extract_user_text(conversation_text)

    hiv_score = compute_hiv_risk(user_text)
    mh_score = compute_mental_health_risk(user_text)

    return ConversationRiskResult(
        conversation_id=conversation_id,
        hiv_risk_score=round(hiv_score, 2),
        hiv_risk_level=risk_level(hiv_score),
        mental_health_risk_score=round(mh_score, 2),
        mental_health_risk_level=risk_level(mh_score),
        hiv_recommendation=generate_hiv_recommendation(hiv_score),
        mental_health_recommendation=generate_mental_health_recommendation(mh_score),
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

if __name__ == "__main__":
    DATA_PATH = "health_ai_whatsapp_100_conversations_long.txt"  # local path

    conversations = load_conversations(DATA_PATH)

    results = []
    for idx, conv in enumerate(conversations):
        out = analyse_conversation(idx, conv)
        results.append({
            "conversation_id": out.conversation_id,
            "hiv_risk_score": out.hiv_risk_score,
            "hiv_risk_level": out.hiv_risk_level,
            "mental_health_risk_score": out.mental_health_risk_score,
            "mental_health_risk_level": out.mental_health_risk_level,
            "hiv_recommendation": out.hiv_recommendation,
            "mental_health_recommendation": out.mental_health_recommendation,
        })

    df = pd.DataFrame(results)
    df.to_csv("conversation_risk_results.csv", index=False)

    print("Analysis complete. Saved to conversation_risk_results.csv")
