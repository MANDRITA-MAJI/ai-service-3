from fastapi import APIRouter, HTTPException
from app.models.triage_confirm import ConfirmVagueRequest, ConfirmVagueResponse
from app.services import triage_service
from app.db.chroma_client import get_or_create_collection

router = APIRouter()


@router.post("/confirm-vague", response_model=ConfirmVagueResponse)
def confirm_vague(payload: ConfirmVagueRequest):
    """
    Called by the BACKEND — not triggered by AI on its own — when a
    professor rejects a "doubtful" problem as not-actually-research.

    We don't ask the backend to resend the problem text. The submission's
    embedding was already stored in the `complaints` collection when it
    was first routed (see pipeline.py, "routed" outcome) — so we just
    fetch that same vector back out and store it in the confirmed_vague
    set. No re-embedding, no LLM call, no risk of drifting from the
    original text.
    """
    collection = get_or_create_collection("complaints")
    result = collection.get(ids=[payload.submission_id], include=["embeddings"])

    if not result["ids"]:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No stored embedding found for {payload.submission_id}. "
                "This submission may never have reached the 'routed' outcome "
                "through /process — only routed submissions get their "
                "embedding stored."
            ),
        )

    vector = result["embeddings"][0]
    triage_service.store_confirmed_vague(
        submission_id=payload.submission_id,
        vector=vector,
        confirmed_by=payload.confirmed_by,
        reason=payload.reason,
    )

    return ConfirmVagueResponse(submission_id=payload.submission_id, status="added_to_vague_set")
