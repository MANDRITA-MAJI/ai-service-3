from dotenv import load_dotenv
load_dotenv()

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
WHISPER_MODEL_SIZE = "small"

CHROMA_PERSIST_DIR = str(BASE_DIR.parent / "chroma_db")

# similarity thresholds — same 0.85 cutoff reused everywhere so every
# module agrees on what "the same thing" means
DEDUP_SIMILARITY_THRESHOLD = 0.85
VAGUE_MATCH_THRESHOLD = 0.85
ROUTING_TOP_K = 5

TRANSCRIPTION_CONFIDENCE_HIGH = 0.85
TRANSCRIPTION_CONFIDENCE_MEDIUM = 0.5
