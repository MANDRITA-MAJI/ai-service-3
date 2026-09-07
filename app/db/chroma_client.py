import chromadb
from app.config import CHROMA_PERSIST_DIR

_client = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _client


def get_or_create_collection(name: str):
    client = get_client()
    # IMPORTANT: default Chroma distance is squared L2, not cosine —
    # this must be set explicitly or your similarity math won't match
    # what we calculated by hand earlier in the conversation
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
