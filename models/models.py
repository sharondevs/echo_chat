from pydantic import BaseModel, Field
from typing import Optional, List, Any
from enum import Enum

class QueryMode(str, Enum):
    RESUME = "resume"
    DOCUMENTS = "documents"
    


class DocumentUploadResponse(BaseModel):
    message: str = Field(..., description="Upload status message")
    file_count: int = Field(..., description="Number of files processed")
    session_id: Optional[str] = Field(None, description="Session ID")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    modes_available: List[str] = Field(..., description="Available query modes") 