import uuid
from datetime import datetime
 
from pydantic import BaseModel, ConfigDict
 
from app.models.enums import AssetStatus, JobStatus
 
 
class ErrorResponse(BaseModel):
    detail: str
 
 
class VideoAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 
    id: uuid.UUID
    filename: str
    status: AssetStatus
    mime_type: str
    file_size_bytes: int
    duration_seconds: float | None = None
    thumbnail_path: str | None = None
    created_at: datetime
    updated_at: datetime
 
class ProcessingJobBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 
    id: uuid.UUID
    status: JobStatus
    created_at: datetime
 
 
class UploadResponse(BaseModel):
    asset_id: uuid.UUID
    job_id: uuid.UUID
    status: AssetStatus
    filename: str
   