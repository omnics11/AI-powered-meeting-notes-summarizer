# app/schemas.py
from pydantic import BaseModel

class GenerateRequest(BaseModel):
    instruction: str
    transcript: str

class UpdateSummaryRequest(BaseModel):
    summary: str
    recipients: str  # comma separated emails
