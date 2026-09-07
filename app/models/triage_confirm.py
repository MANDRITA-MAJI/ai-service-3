from pydantic import BaseModel


class ConfirmVagueRequest(BaseModel):
    submission_id: str
    confirmed_by: str          # university_id (or dept id) of the professor who rejected it
    reason: str = "not_innovative"


class ConfirmVagueResponse(BaseModel):
    submission_id: str
    status: str
