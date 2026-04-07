"""
File Upload Endpoints

Handles bank statement and financial document uploads with
parsing and automatic transaction extraction.
"""

from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, status, BackgroundTasks
from uuid import UUID

from app.api.deps import DbSession, CurrentUser
from app.schemas.transaction import TransactionResponse
from app.services.upload_service import UploadService
from app.config import settings


router = APIRouter()


@router.post("", response_model=dict)
async def upload_statement(
    file: UploadFile = File(..., description="Bank statement file (PDF, CSV, Excel)"),
    db: DbSession = None,
    current_user: CurrentUser = None,
    background_tasks: BackgroundTasks = None,
):
    """
    Upload a bank statement for processing.
    
    Accepts PDF, CSV, and Excel files. Transactions are extracted
    asynchronously and categorized using ML models.
    
    Args:
        file: Uploaded file
        db: Database session
        current_user: Authenticated user
        background_tasks: FastAPI background tasks
        
    Returns:
        dict: Upload status and job ID
        
    Raises:
        HTTPException: 400 if file type not supported or file too large
    """
    # Validate file extension
    file_ext = f".{file.filename.split('.')[-1].lower()}"
    if file_ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {settings.ALLOWED_UPLOAD_EXTENSIONS}"
        )
    
    # Validate file size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Reset file position for processing
    await file.seek(0)
    
    upload_service = UploadService(db)
    
    # Create upload job
    job = await upload_service.create_upload_job(
        user_id=current_user.id,
        filename=file.filename,
        file_size=len(contents),
    )
    
    # Process file in background
    background_tasks.add_task(
        upload_service.process_upload,
        job_id=job.id,
        user_id=current_user.id,
        file_content=contents,
        file_type=file_ext,
    )
    
    return {
        "message": "File uploaded successfully. Processing started.",
        "job_id": str(job.id),
        "filename": file.filename,
        "status": "processing"
    }


@router.get("/jobs", response_model=List[dict])
async def list_upload_jobs(
    db: DbSession,
    current_user: CurrentUser,
):
    """
    List all upload jobs for the current user.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List[dict]: Upload job statuses
    """
    upload_service = UploadService(db)
    jobs = await upload_service.list_jobs(user_id=current_user.id)
    return jobs


@router.get("/jobs/{job_id}", response_model=dict)
async def get_upload_job_status(
    job_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Get status of a specific upload job.
    
    Args:
        job_id: Upload job UUID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        dict: Job status and results
        
    Raises:
        HTTPException: 404 if job not found
    """
    upload_service = UploadService(db)
    job = await upload_service.get_job_status(
        job_id=job_id,
        user_id=current_user.id,
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload job not found"
        )
    
    return job


@router.get("/jobs/{job_id}/transactions", response_model=List[TransactionResponse])
async def get_job_transactions(
    job_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Get transactions extracted from an upload job.
    
    Args:
        job_id: Upload job UUID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List[TransactionResponse]: Extracted transactions
        
    Raises:
        HTTPException: 404 if job not found
    """
    upload_service = UploadService(db)
    transactions = await upload_service.get_job_transactions(
        job_id=job_id,
        user_id=current_user.id,
    )
    
    if transactions is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload job not found"
        )
    
    return transactions


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload_job(
    job_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Delete an upload job and its associated data.
    
    Args:
        job_id: Upload job UUID
        db: Database session
        current_user: Authenticated user
        
    Raises:
        HTTPException: 404 if job not found
    """
    upload_service = UploadService(db)
    deleted = await upload_service.delete_job(
        job_id=job_id,
        user_id=current_user.id,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload job not found"
        )
