from pydantic import BaseModel

class TranscriptResponse(BaseModel):
    transcript: str

class SummaryResponse(BaseModel):
    summary: str
