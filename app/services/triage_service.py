from app.db.chroma_client import get_or_create_collection
from app.config import VAGUE_MATCH_THRESHOLD
from app.services.llm_client import call_json

VAGUE_COLLECTION_NAME = "confirmed_vague"


def check_known_vague(vector: list, top_k: int = 1) -> dict | None:
    """Cheap first check — does this problem closely match something a
    university/PRI/ULB has already confirmed as advisory/vague? No LLM
    call needed here; this is pure embedding similarity, same mechanism
    as dedup."""
    collection = get_or_create_collection(VAGUE_COLLECTION_NAME)
    if collection.count() == 0:
        return None

    results = collection.query(query_embeddings=[vector], n_results=top_k)
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]
    if not distances:
        return None

    similarity = 1 - distances[0]
    if similarity >= VAGUE_MATCH_THRESHOLD:
        return {"matched_id": ids[0], "score": round(similarity, 3)}
    return None


def store_confirmed_vague(submission_id: str, vector: list, confirmed_by: str, reason: str):
    """Call this once a university/PRI/ULB confirms a problem is genuinely
    vague — no LLM re-check needed, just embed and store directly."""
    collection = get_or_create_collection(VAGUE_COLLECTION_NAME)
    collection.add(
        embeddings=[vector],
        metadatas=[{"confirmed_by": confirmed_by, "reason": reason}],
        ids=[submission_id],
    )


TRIAGE_SYSTEM_PROMPT = (
    "You assess whether a citizen-submitted civic problem needs academic "
    "research, or can be resolved through an existing advisory service. "
    "Always respond with strict JSON only, no extra text, no markdown "
    "formatting."
)


def llm_triage(text: str, category: str) -> dict:
    """Only reached for genuinely novel cases that didn't match the
    confirmed-vague set above — this LLM call can STILL return "advisory"
    even though nothing matched yet, since it may be a first-of-its-kind
    vague problem."""
    user_prompt = f"""Problem: "{text}"
Category: {category}

Classify as exactly one of:
- "advisory": individual-scale issue, or has a well-established solution
  pathway through existing services (agricultural extension, health
  worker, local repair department)
- "research": systemic/novel issue affecting a community, no established
  solution — needs investigation or new technology
- "doubtful": genuinely unclear, needs a human (university) to confirm
  before proceeding

Also decide needs_govt_supervision: true if implementing a solution would
require public land access, government scheme coordination, or civic
infrastructure changes.

Return JSON in exactly this shape:
{{
  "classification": "advisory" | "doubtful" | "research",
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence>",
  "needs_govt_supervision": true | false
}}"""

    try:
        result = call_json(TRIAGE_SYSTEM_PROMPT, user_prompt)
        if result.get("classification") not in ("advisory", "doubtful", "research"):
            raise ValueError("LLM returned an invalid classification")
        result.setdefault("needs_confirmation", False)
        return result
    except Exception as e:
        # fail safe: if the LLM call breaks, don't silently auto-approve
        # or auto-reject — default to "doubtful" so a human reviews it
        print(f"[triage_service] LLM call failed: {e}") 
        return {
            "classification": "doubtful",
            "confidence": 0.0,
            "reasoning": "LLM triage call failed — defaulting to human review",
            "needs_govt_supervision": False,
            "needs_confirmation": True,
        }
