from typing import Optional, List, Literal
from pydantic import BaseModel


class SubmittedBy(BaseModel):
    user_id: str
    role: Literal["citizen", "panchayat", "ulb"]


class Content(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None   # filled by backend for text input; may be empty for voice until transcribed
    language: Optional[str] = None
    audio_url: Optional[str] = None     # present only when input_type = "voice"


class Coordinates(BaseModel):
    lat: float
    lng: float


class Location(BaseModel):
    state: str
    district: str
    area_type: Literal["rural", "urban"]
    block: Optional[str] = None
    panchayat_id: Optional[str] = None
    village: Optional[str] = None
    ulb_id: Optional[str] = None
    ward_no: Optional[str] = None
    pincode: str
    coordinates: Coordinates
    address_text: Optional[str] = None


class MediaItem(BaseModel):
    type: Literal["image", "video", "document"]
    url: str


class SubmissionInput(BaseModel):
    submission_id: str
    submitted_by: SubmittedBy
    input_type: Literal["text", "voice"]
    content: Content
    location: Location
    media: List[MediaItem] = []
    submitted_at: str
