from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "ObserveLite"


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2_000, examples=["I love this simple observability demo."])


class PredictResponse(BaseModel):
    sentiment: str
    confidence: float
    input_length: int

