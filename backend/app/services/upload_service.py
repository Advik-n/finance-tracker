"""
Upload Service

Handles file upload processing and transaction extraction.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.parsers.pdf_parser import PDFParser
from app.parsers.csv_parser import CSVParser
from app.parsers.excel_parser import ExcelParser
from app.ml.categorizer import TransactionCategorizer


class UploadJob:
    """Upload job data class."""
    
    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        filename: str,
        file_size: int,
        status: str = "pending",
    ):
        self.id = id
        self.user_id = user_id
        self.filename = filename
        self.file_size = file_size
        self.status = status
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.transactions_count: int = 0
        self.error_message: Optional[str] = None


class UploadService:
    """
    Service class for file upload operations.
    
    Handles parsing bank statements and extracting transactions.
    """
    
    # In-memory job storage (use Redis or DB in production)
    _jobs: dict = {}
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pdf_parser = PDFParser()
        self.csv_parser = CSVParser()
        self.excel_parser = ExcelParser()
        self.categorizer = TransactionCategorizer()
    
    async def create_upload_job(
        self,
        user_id: UUID,
        filename: str,
        file_size: int,
    ) -> UploadJob:
        """
        Create a new upload job.
        
        Args:
            user_id: User UUID
            filename: Original filename
            file_size: File size in bytes
            
        Returns:
            Created UploadJob
        """
        job = UploadJob(
            id=uuid4(),
            user_id=user_id,
            filename=filename,
            file_size=file_size,
        )
        self._jobs[str(job.id)] = job
        return job
    
    async def process_upload(
        self,
        job_id: UUID,
        user_id: UUID,
        file_content: bytes,
        file_type: str,
    ) -> None:
        """
        Process uploaded file and extract transactions.
        
        Args:
            job_id: Upload job UUID
            user_id: User UUID
            file_content: Raw file bytes
            file_type: File extension
        """
        job = self._jobs.get(str(job_id))
        if not job:
            return
        
        try:
            job.status = "processing"
            
            # Parse file based on type
            if file_type == ".pdf":
                raw_transactions = self.pdf_parser.parse(file_content)
            elif file_type == ".csv":
                raw_transactions = self.csv_parser.parse(file_content)
            elif file_type in [".xlsx", ".xls"]:
                raw_transactions = self.excel_parser.parse(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Create transactions
            transactions = []
            for raw in raw_transactions:
                transaction = Transaction(
                    user_id=user_id,
                    amount=Decimal(str(raw.get("amount", 0))),
                    currency=raw.get("currency", "USD"),
                    transaction_date=raw.get("date"),
                    description=raw.get("description", ""),
                    merchant_name=raw.get("merchant"),
                    transaction_type=raw.get("type", "expense"),
                    source="upload",
                    upload_job_id=job_id,
                )
                
                # Auto-categorize
                category_id, confidence = self.categorizer.predict(
                    description=transaction.description,
                    merchant_name=transaction.merchant_name,
                    amount=float(transaction.amount),
                    categories=[],  # Would load from DB
                )
                
                if category_id:
                    transaction.category_id = category_id
                    transaction.is_auto_categorized = True
                    transaction.categorization_confidence = Decimal(str(confidence))
                
                self.db.add(transaction)
                transactions.append(transaction)
            
            await self.db.flush()
            
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.transactions_count = len(transactions)
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
    
    async def list_jobs(self, user_id: UUID) -> List[dict]:
        """
        List upload jobs for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of job dictionaries
        """
        user_jobs = [
            job for job in self._jobs.values()
            if job.user_id == user_id
        ]
        
        return [
            {
                "id": str(job.id),
                "filename": job.filename,
                "file_size": job.file_size,
                "status": job.status,
                "transactions_count": job.transactions_count,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
            }
            for job in sorted(user_jobs, key=lambda j: j.created_at, reverse=True)
        ]
    
    async def get_job_status(
        self,
        job_id: UUID,
        user_id: UUID,
    ) -> Optional[dict]:
        """
        Get status of a specific job.
        
        Args:
            job_id: Upload job UUID
            user_id: User UUID
            
        Returns:
            Job status dictionary
        """
        job = self._jobs.get(str(job_id))
        if not job or job.user_id != user_id:
            return None
        
        return {
            "id": str(job.id),
            "filename": job.filename,
            "file_size": job.file_size,
            "status": job.status,
            "transactions_count": job.transactions_count,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        }
    
    async def get_job_transactions(
        self,
        job_id: UUID,
        user_id: UUID,
    ) -> Optional[List[Transaction]]:
        """
        Get transactions from an upload job.
        
        Args:
            job_id: Upload job UUID
            user_id: User UUID
            
        Returns:
            List of transactions
        """
        job = self._jobs.get(str(job_id))
        if not job or job.user_id != user_id:
            return None
        
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.upload_job_id == job_id)
            .order_by(Transaction.transaction_date.desc())
        )
        
        return list(result.scalars().all())
    
    async def delete_job(
        self,
        job_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete an upload job and its transactions.
        
        Args:
            job_id: Upload job UUID
            user_id: User UUID
            
        Returns:
            True if deleted
        """
        job = self._jobs.get(str(job_id))
        if not job or job.user_id != user_id:
            return False
        
        # Delete associated transactions
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.upload_job_id == job_id)
        )
        transactions = result.scalars().all()
        
        for transaction in transactions:
            await self.db.delete(transaction)
        
        await self.db.flush()
        
        # Remove job
        del self._jobs[str(job_id)]
        
        return True
