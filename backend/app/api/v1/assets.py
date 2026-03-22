from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.storage import store_file
from app.schemas.assets import ErrorResponse, UploadResponse
from app.services.assets import create_asset_with_job
from app.services.validation import ValidationError, validate_upload
from app.workers.tasks import process_video

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
    responses={400: {"model": ErrorResponse}},
)
async def upload_video(file: UploadFile, db: Session = Depends(get_db)):
    """Handle the upload of a video file and start a processing job"""

    try:
        contents = await validate_upload(file)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.detail)

    filename = file.filename or "Unknown"
    mime_type = file.content_type or "application/octet-stream"
    storage_path = store_file(
        file_bytes=contents, filename=filename, content_type=mime_type
    )

    asset, job = create_asset_with_job(
        db,
        filename,
        storage_path=storage_path,
        mime_type=mime_type,
        file_size_bytes=len(contents),
    )

    process_video.delay(str(asset.id), str(job.id))

    return UploadResponse(
        asset_id=asset.id, job_id=job.id, status=asset.status, filename=asset.filename
    )
