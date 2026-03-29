import os
import tempfile
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

SUPPORTED_FORMATS = [".mp3", ".wav", ".m4a", ".mp4", ".ogg", ".webm", ".mpeg", ".mpga"]

LANGUAGE_CODES = {
    "Auto-detect": None,
    "Hindi":    "hi",
    "Marathi":  "mr",
    "Tamil":    "ta",
    "Telugu":   "te",
    "Bengali":  "bn",
    "Gujarati": "gu",
    "English":  "en",
}


def transcribe_audio(audio_bytes: bytes, filename: str, language_hint: str = "Auto-detect") -> dict:
    ext = os.path.splitext(filename)[1].lower() or ".mp3"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            kwargs = {
                "model": "whisper-large-v3",
                "file": f,
                "response_format": "verbose_json",
            }
            lang_code = LANGUAGE_CODES.get(language_hint)
            if lang_code:
                kwargs["language"] = lang_code

            result = client.audio.transcriptions.create(**kwargs)

        segments = getattr(result, "segments", []) or []
        duration = segments[-1].get("end", 0) if segments else 0
        dur_str  = f"{int(duration//60)}m {int(duration%60)}s" if duration else "unknown"

        return {
            "transcript":    result.text.strip(),
            "language":      getattr(result, "language", "unknown"),
            "duration":      dur_str,
            "segment_count": len(segments),
            "success":       True,
        }

    except Exception as e:
        return {
            "transcript": "", "language": "unknown",
            "duration": "unknown", "segment_count": 0,
            "success": False, "error": str(e),
        }
    finally:
        os.unlink(tmp_path)


