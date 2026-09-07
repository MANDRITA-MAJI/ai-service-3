from app.db.chroma_client import get_or_create_collection
from app.config import DEDUP_SIMILARITY_THRESHOLD

COLLECTION_NAME = "complaints"


def find_duplicates(vector: list, category: str, district: str, top_k: int = 5) -> list:
    collection = get_or_create_collection(COLLECTION_NAME)
    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[vector],
        n_results=top_k,
        where={
            "$and": [
                {"category": {"$eq": category}},
                {"district": {"$eq": district}},
            ]
        },
    )

    matches = []
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    for sub_id, distance in zip(ids, distances):
        similarity = 1 - distance  # cosine space: distance = 1 - similarity
        if similarity >= DEDUP_SIMILARITY_THRESHOLD:
            matches.append({"submission_id": sub_id, "similarity": round(similarity, 3)})
    return matches


def store_embedding(submission_id: str, vector: list, category: str, district: str):
    """Call this only for non-duplicate, non-advisory submissions —
    so future dedup checks can find this one."""
    collection = get_or_create_collection(COLLECTION_NAME)
    collection.add(
        embeddings=[vector],
        metadatas=[{"category": category, "district": district}],
        ids=[submission_id],
    )
