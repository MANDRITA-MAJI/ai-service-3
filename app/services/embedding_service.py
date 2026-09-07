from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL_NAME

_model = None


def load_model():
    """Called once at FastAPI startup (see main.py lifespan) — never per-request."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def embed_text(text: str) -> list:
    model = load_model()
    return model.encode(text).tolist()


def build_embedding_text(title: str | None, description: str) -> str:
    """The one function every module should call before embedding —
    keeps title+description joining consistent everywhere."""
    title = title or ""
    return f"{title}. {description}".strip(". ")
