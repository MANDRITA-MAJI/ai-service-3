import numpy as np
from faster_whisper import WhisperModel
from app.config import (
    WHISPER_MODEL_SIZE,
    TRANSCRIPTION_CONFIDENCE_HIGH,
    TRANSCRIPTION_CONFIDENCE_MEDIUM,
)

_model = None


def load_model():
    """Called once at FastAPI startup — self-hosted, so no per-request
    cost and no risk of running out of API tokens during the demo."""
    global _model
    if _model is None:
        _model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def confidence_tier(score: float) -> str:
    if score > TRANSCRIPTION_CONFIDENCE_HIGH:
        return "high"
    if score >= TRANSCRIPTION_CONFIDENCE_MEDIUM:
        return "medium"
    return "low"


def transcribe_audio(audio_path: str, force_english: bool = True) -> dict:
    """audio_path must be a local file path. Translates to English by default."""
    model = load_model()
    
    # NEW: Tell Whisper to translate to English instead of just transcribing
    task = "translate" if force_english else "transcribe"
    segments, info = model.transcribe(audio_path, task=task)
    
    segment_list = list(segments)

    if not segment_list:
        return {
            "text": "",
            "detected_language": info.language,
            "language_confidence": info.language_probability,
            "transcription_confidence": 0.0,
            "confidence_tier": "low",
            "silence_detected": True,
            "translated_to_english": force_english # New tracking field
        }

    text = " ".join(s.text.strip() for s in segment_list).strip()
    avg_conf = float(np.mean([np.exp(s.avg_logprob) for s in segment_list]))
    silence = any(s.no_speech_prob > 0.6 for s in segment_list)

    return {
        "text": text,
        "detected_language": info.language,
        "language_confidence": info.language_probability,
        "transcription_confidence": round(avg_conf, 3),
        "confidence_tier": confidence_tier(avg_conf),
        "silence_detected": silence,
        "translated_to_english": force_english # New tracking field
    }


def download_audio(url: str, dest_dir: str = "/tmp") -> str:
    """TODO: wire this to whatever storage your backend uses (S3, GCS,
    Next.js public upload folder, etc). Placeholder using plain HTTP GET —
    replace with your actual storage client if audio isn't reachable
    over a plain URL."""
    import requests
    import uuid
    import os

    local_path = os.path.join(dest_dir, f"{uuid.uuid4().hex}.audio")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(response.content)
    return local_path
