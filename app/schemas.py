from pydantic import BaseModel, Field


class AllocRequest(BaseModel):
    request_id: str = Field(..., min_length=1, description="Unique request identifier")
    token_count: int = Field(..., gt=0, description="Number of tokens requested")


class AllocResponse(BaseModel):
    node_id: int
    remaining_quota: int


class FreeRequest(BaseModel):
    request_id: str = Field(..., min_length=1)


class FreeResponse(BaseModel):
    node_id: int


class ErrorResponse(BaseModel):
    error: str
