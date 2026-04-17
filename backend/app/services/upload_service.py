"""
Upload Service

Handles file upload processing and transaction extraction.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction, TransactionSource, TransactionType
from app.models.category import Category
from app.parsers.universal_parser import parse_statement
from app.ml.categorizer import TransactionCategorizer, TransactionInput
from app.services.transaction_service import TransactionService


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
        self.categorizer = TransactionCategorizer()
        self.transaction_service = TransactionService(db)

    def _map_source(self, file_type: str) -> TransactionSource:
        ext = file_type.lower().lstrip(".")
        if ext == "pdf":
            return TransactionSource.PDF
        if ext == "csv":
            return TransactionSource.CSV
        if ext in {"xlsx", "xls", "xlsm"}:
            return TransactionSource.EXCEL
        return TransactionSource.API
    
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

            parser_result = parse_statement(
                file_content=file_content,
                filename=job.filename,
                file_type=file_type.lstrip("."),
            )
            if parser_result.errors:
                raise ValueError("; ".join(parser_result.errors))

            categories_result = await self.db.execute(
                select(Category).where(
                    or_(
                        Category.user_id == user_id,
                        Category.is_system == True,  # noqa: E712
                    )
                )
            )
            categories = list(categories_result.scalars().all())

            transactions = []
            for parsed in parser_result.transactions:
                txn_type_value = getattr(parsed.transaction_type, "value", parsed.transaction_type)
                if txn_type_value == TransactionType.CREDIT.value:
                    txn_type = TransactionType.CREDIT
                elif txn_type_value == TransactionType.DEBIT.value:
                    txn_type = TransactionType.DEBIT
                else:
                    txn_type = TransactionType.DEBIT

                transaction_date = datetime.strptime(parsed.date, "%Y-%m-%d")
                merchant_name = self.categorizer.extract_merchant(parsed.description) or parsed.description
                transaction = Transaction(
                    user_id=user_id,
                    amount=Decimal(str(parsed.amount)),
                    transaction_date=transaction_date,
                    description=parsed.description,
                    merchant_name=merchant_name,
                    transaction_type=txn_type,
                    source=self._map_source(file_type),
                    upload_batch_id=job_id,
                    raw_data=parsed.to_dict(),
                )

                if categories:
                    result = self.categorizer.categorize(
                        TransactionInput(
                            description=parsed.description,
                            amount=float(parsed.amount),
                            transaction_type=txn_type.value.lower(),
                            date=transaction_date,
                        )
                    )
                    category_id = self.transaction_service._resolve_category_id(
                        categories=categories,
                        category_name=result.category,
                        subcategory_name=result.subcategory,
                    )
                    if category_id:
                        transaction.category_id = category_id
                        transaction.is_auto_categorized = True
                        transaction.confidence_score = float(result.confidence)

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
            .where(
                Transaction.upload_batch_id == job_id,
                Transaction.is_deleted == False,  # noqa: E712
            )
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
            .where(Transaction.upload_batch_id == job_id)
        )
        transactions = result.scalars().all()
        
        for transaction in transactions:
            await self.db.delete(transaction)
        
        await self.db.flush()
        
        # Remove job
        del self._jobs[str(job_id)]
        
        return True
