from fastapi import APIRouter
from app.models.submission import SubmissionInput
from app.models.pipeline_output import ProcessResponse
from app.services import (
    speech_service,
    embedding_service,
    classification_service,
    triage_service,
    dedup_service,
    priority_service,
    routing_service,
)

router = APIRouter()


@router.post("/process", response_model=ProcessResponse)
def process_submission(submission: SubmissionInput):
    # ---- Step 1: resolve text (transcribe if voice) ----
    description = submission.content.description
    transcription_result = None

    if submission.input_type == "voice" and submission.content.audio_url:
        local_path = speech_service.download_audio(submission.content.audio_url)
        transcription_result = speech_service.transcribe_audio(local_path)
        description = transcription_result["text"]

    embedding_text = embedding_service.build_embedding_text(
        submission.content.title, description
    )
    vector = embedding_service.embed_text(embedding_text)

    # ---- Step 2: classification ----
    classification = classification_service.classify_problem(embedding_text)
    category = classification["primary_category"]

    # ---- Step 3: vague check — cheap semantic match FIRST ----
    known_vague_match = triage_service.check_known_vague(vector)

    if known_vague_match is not None:
        return ProcessResponse(
            submission_id=submission.submission_id,
            outcome="advisory",
            classification=classification,
            triage={
                "classification": "advisory",
                "confidence": known_vague_match["score"],
                "reasoning": "Matches a previously confirmed advisory/vague problem",
                "needs_govt_supervision": False,
                "needs_confirmation": False,
            },
            transcription=transcription_result,
        )

    # ---- Step 4: LLM triage — second check, only for novel cases ----
    # NOTE: llm_triage can ALSO return "advisory" here — a novel problem
    # that didn't match anything in the confirmed-vague set can still
    # turn out to be advisory. Don't assume everything reaching this
    # point is automatically research-worthy.
    triage_result = triage_service.llm_triage(embedding_text, category)

    if triage_result["classification"] == "advisory":
        return ProcessResponse(
            submission_id=submission.submission_id,
            outcome="advisory",
            classification=classification,
            triage=triage_result,
            transcription=transcription_result,
        )

    # "doubtful" carries needs_confirmation=True downstream so the
    # university dashboard knows to ask "confirm this needs research?"
    if triage_result["classification"] == "doubtful":
        triage_result["needs_confirmation"] = True

    # ---- Step 5: deduplication ----
    duplicates = dedup_service.find_duplicates(vector, category, submission.location.district)

    if duplicates:
        return ProcessResponse(
            submission_id=submission.submission_id,
            outcome="duplicate",
            classification=classification,
            triage=triage_result,
            duplicate_info={"similar_submission_ids": duplicates},
            transcription=transcription_result,
        )

    # ---- Step 6: priority ----
    priority = priority_service.compute_priority(
        description=description,
        category=category,
        duplicate_count=1,  # starts at 1; batch clustering job updates this later
        submitted_at=submission.submitted_at,
        has_media=len(submission.media) > 0,
    )

    # ---- Step 7: university routing ----
    routing = routing_service.match_universities(vector, category, submission.location.district)

    # store this submission's embedding so FUTURE submissions can be
    # checked against it during dedup
    dedup_service.store_embedding(
        submission.submission_id, vector, category, submission.location.district
    )

    return ProcessResponse(
        submission_id=submission.submission_id,
        outcome="routed",
        classification=classification,
        triage=triage_result,
        priority=priority,
        routing=routing,
        transcription=transcription_result,
    )
