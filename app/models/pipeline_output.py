from typing import Optional, List, Literal
from pydantic import BaseModel


class CategoryResult(BaseModel):
    label: str
    confidence: float


class ClassificationOutput(BaseModel):
    categories: List[CategoryResult]
    primary_category: str


class TriageOutput(BaseModel):
    # "doubtful" is your "uncertain" tier — problem still proceeds through
    # the pipeline, but needs_confirmation tells the university dashboard
    # to ask "is this really worth researching?" instead of a normal offer
    classification: Literal["advisory", "doubtful", "research"]
    confidence: float
    reasoning: str
    needs_govt_supervision: bool = False
    needs_confirmation: bool = False


class DuplicateMatch(BaseModel):
    submission_id: str
    similarity: float


class DuplicateInfo(BaseModel):
    similar_submission_ids: List[DuplicateMatch]


class PriorityOutput(BaseModel):
    score: float
    tier: Literal["high", "medium", "low"]


class UniversityMatch(BaseModel):
    university_id: str
    department: str
    specialization: str
    score: float
    rank: int  # 1..5 - the order the backend should try them in
    status: str  # "pending" for all 5; backend flips this as it works through the sequence


class RoutingOutput(BaseModel):
    shortlist: List[UniversityMatch]


class TranscriptionOutput(BaseModel):
    text: str
    detected_language: Optional[str] = None
    language_confidence: Optional[float] = None
    transcription_confidence: float
    confidence_tier: Literal["high", "medium", "low"]
    silence_detected: bool


class ProcessResponse(BaseModel):
    submission_id: str
    # tells the backend which branch this submission took —
    # only the fields relevant to that branch will be non-null
    outcome: Literal["advisory", "duplicate", "routed"]

    classification: Optional[ClassificationOutput] = None
    triage: Optional[TriageOutput] = None
    duplicate_info: Optional[DuplicateInfo] = None
    priority: Optional[PriorityOutput] = None
    routing: Optional[RoutingOutput] = None
    transcription: Optional[TranscriptionOutput] = None
