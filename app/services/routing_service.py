from app.db.chroma_client import get_or_create_collection
from app.config import ROUTING_TOP_K

COLLECTION_NAME = "university_departments"


def match_universities(vector: list, category: str, district: str, top_k: int = ROUTING_TOP_K) -> dict:
    collection = get_or_create_collection(COLLECTION_NAME)
    if collection.count() == 0:
        return {"shortlist": []}

    # pull more than top_k so the hard-filter boosts below can re-rank
    # before we cut down to the final shortlist
    results = collection.query(query_embeddings=[vector], n_results=top_k * 2)

    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    candidates = []
    for uid, distance, meta in zip(ids, distances, metadatas):
        similarity = 1 - distance
        score = similarity

        if meta.get("category") == category:
            score += 0.1

        if meta.get("current_active_projects", 0) >= meta.get("max_concurrent_projects", 999):
            score -= 0.5  # effectively disqualifies universities at capacity

        if meta.get("district") == district:
            score += 0.05

        candidates.append({
            "university_id": meta.get("university_id"),
            "department": meta.get("department"),
            "specialization": meta.get("specialization", ""),
            "score": round(score, 3),
        })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    shortlist = candidates[:top_k]

    # rank is the order the backend should try them in. Status starts as
    # "pending" for all five; the backend updates it as it works through the list.
    for rank, c in enumerate(shortlist, start=1):
        c["rank"] = rank
        c["status"] = "pending"

    return {"shortlist": shortlist}
