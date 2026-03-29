import json
import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_groq_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        api_key = os.environ.get("GROQ_API_KEY", "")
    return Groq(api_key=api_key)

client = get_groq_client()

SYSTEM_PROMPT = """You are an expert AI system for detecting phishing and scam messages in Indian languages and English.

IMPORTANT SCORING RULES - follow these strictly:
- "safe" + scam_probability 0-30: Normal messages, delivery updates, OTP you requested yourself, bank transaction alerts with no action required, casual conversation
- "suspicious" + scam_probability 31-65: Has one or two mild red flags but not clearly a scam
- "high_risk" + scam_probability 66-100: Clear scam — asks for OTP/PIN/password, threatens account closure, promises fake prize, impersonates authority AND demands action

DO NOT mark something high_risk just because it mentions a bank or OTP. A message saying "Your OTP is 123456" that the user requested is SAFE.

Common Indian scam patterns to detect:
- Asking you to SHARE your OTP to someone else (scam) vs receiving an OTP (safe)
- Fake bank/KYC alerts threatening account closure unless you call a number
- Lottery/prize scams asking for personal details to claim prize
- Urgency + threat + action demand together = high risk
- Authority impersonation (RBI, CBI, SBI, police) demanding payment or info

You must respond ONLY with a valid JSON object. No markdown, no extra text.

{
  "risk_level": "safe" | "suspicious" | "high_risk",
  "scam_probability": <integer 0-100>,
  "language_detected": "<full language name>",
  "summary": "<2-3 clear sentences explaining your verdict>",
  "red_flags": ["<flag1>", "<flag2>"],
  "highlights": [
    {
      "phrase": "<exact substring from the original text>",
      "reason": "<why this phrase is suspicious>"
    }
  ],
  "tactics": {
    "Urgency / Time pressure": <0-10>,
    "Fear / Threat": <0-10>,
    "Authority impersonation": <0-10>,
    "OTP / Password request": <0-10>,
    "Fake reward / Prize": <0-10>,
    "Personal info request": <0-10>
  },
  "suspicious_links": [],
  "recommendation": "<one clear actionable sentence>"
}"""

def analyze_message(text: str, source_type: str = "text") -> dict:
    label = "audio transcript" if source_type == "audio_transcript" else "text message"
    user_content = f"Analyze this {label} for phishing/scam intent:\n\n{text}"

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_content},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model adds them
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        result["_raw_text"] = text
        result["_source_type"] = source_type
        return result

    except json.JSONDecodeError as e:
        return _fallback(text, source_type, f"JSON parse error: {e}")
    except Exception as e:
        raise RuntimeError(f"Groq API error: {e}")


def _fallback(text, source_type, reason):
    return {
        "risk_level": "suspicious",
        "scam_probability": 50,
        "language_detected": "Unknown",
        "summary": f"Analysis completed but response could not be parsed. Reason: {reason}",
        "red_flags": ["Could not fully parse AI response"],
        "highlights": [],
        "tactics": {
            "Urgency / Time pressure": 0,
            "Fear / Threat": 0,
            "Authority impersonation": 0,
            "OTP / Password request": 0,
            "Fake reward / Prize": 0,
            "Personal info request": 0,
        },
        "suspicious_links": [],
        "recommendation": "Review this message manually with caution.",
        "_raw_text": text,
        "_source_type": source_type,
    }
