from pydantic import BaseModel


class TextSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionSegment(TextSegment):
    word_timings: list[TextSegment]
