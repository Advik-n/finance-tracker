"""
Transaction Service

Handles transaction CRUD operations and categorization.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionFilter,
)
from app.ml.categorizer import TransactionCategorizer


class TransactionService:
    """
    Service class for transaction operations.
    
    Handles CRUD, filtering, and auto-categorization.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.categorizer = TransactionCategorizer()
    
    async def list_transactions(
        self,
        user_id: UUID,
        filters: TransactionFilter,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[Transaction], int]:
        """
        List transactions with filtering and pagination.
        
        Args:
            user_id: User UUID
            filters: Filter parameters
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (transactions list, total count)
        """
        # Base query
        query = select(Transaction).where(Transaction.user_id == user_id)
        count_query = select(func.count()).select_from(Transaction).where(
            Transaction.user_id == user_id
        )
        
        # Apply filters
        if filters.category_id:
            query = query.where(Transaction.category_id == filters.category_id)
            count_query = count_query.where(Transaction.category_id == filters.category_id)
        
        if filters.start_date:
            query = query.where(Transaction.transaction_date >= filters.start_date)
            count_query = count_query.where(Transaction.transaction_date >= filters.start_date)
        
        if filters.end_date:
            query = query.where(Transaction.transaction_date <= filters.end_date)
            count_query = count_query.where(Transaction.transaction_date <= filters.end_date)
        
        if filters.min_amount is not None:
            query = query.where(Transaction.amount >= filters.min_amount)
            count_query = count_query.where(Transaction.amount >= filters.min_amount)
        
        if filters.max_amount is not None:
            query = query.where(Transaction.amount <= filters.max_amount)
            count_query = count_query.where(Transaction.amount <= filters.max_amount)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            search_filter = or_(
                Transaction.description.ilike(search_term),
                Transaction.merchant_name.ilike(search_term),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if filters.transaction_type:
            query = query.where(Transaction.transaction_type == filters.transaction_type)
            count_query = count_query.where(Transaction.transaction_type == filters.transaction_type)
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        offset = (page - 1) * limit
        query = (
            query
            .options(joinedload(Transaction.category))
            .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        transactions = result.scalars().unique().all()
        
        return list(transactions), total
    
    async def get_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
    ) -> Optional[Transaction]:
        """
        Get a single transaction by ID.
        
        Args:
            transaction_id: Transaction UUID
            user_id: User UUID (for authorization)
            
        Returns:
            Transaction if found and owned by user
        """
        result = await self.db.execute(
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(
                and_(
                    Transaction.id == transaction_id,
                    Transaction.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create_transaction(
        self,
        user_id: UUID,
        data: TransactionCreate,
    ) -> Transaction:
        """
        Create a new transaction with auto-categorization.
        
        Args:
            user_id: User UUID
            data: Transaction data
            
        Returns:
            Created Transaction
        """
        transaction = Transaction(
            user_id=user_id,
            amount=data.amount,
            currency=data.currency,
            transaction_date=data.transaction_date,
            description=data.description,
            merchant_name=data.merchant_name,
            transaction_type=data.transaction_type,
            notes=data.notes,
            tags=data.tags,
            is_recurring=data.is_recurring,
            source="manual",
        )
        
        # Auto-categorize if no category provided
        if data.category_id:
            transaction.category_id = data.category_id
        else:
            category_id, confidence = await self._auto_categorize(
                description=data.description,
                merchant_name=data.merchant_name,
                amount=data.amount,
                user_id=user_id,
            )
            if category_id:
                transaction.category_id = category_id
                transaction.is_auto_categorized = True
                transaction.categorization_confidence = Decimal(str(confidence))
        
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)
        
        # Load category relationship
        result = await self.db.execute(
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.id == transaction.id)
        )
        return result.scalar_one()
    
    async def create_transactions_bulk(
        self,
        user_id: UUID,
        data: List[TransactionCreate],
    ) -> List[Transaction]:
        """
        Create multiple transactions in bulk.
        
        Args:
            user_id: User UUID
            data: List of transaction data
            
        Returns:
            List of created Transactions
        """
        transactions = []
        
        for item in data:
            transaction = Transaction(
                user_id=user_id,
                amount=item.amount,
                currency=item.currency,
                transaction_date=item.transaction_date,
                description=item.description,
                merchant_name=item.merchant_name,
                transaction_type=item.transaction_type,
                notes=item.notes,
                tags=item.tags,
                is_recurring=item.is_recurring,
                category_id=item.category_id,
                source="bulk",
            )
            
            # Auto-categorize if no category
            if not item.category_id:
                category_id, confidence = await self._auto_categorize(
                    description=item.description,
                    merchant_name=item.merchant_name,
                    amount=item.amount,
                    user_id=user_id,
                )
                if category_id:
                    transaction.category_id = category_id
                    transaction.is_auto_categorized = True
                    transaction.categorization_confidence = Decimal(str(confidence))
            
            self.db.add(transaction)
            transactions.append(transaction)
        
        await self.db.flush()
        
        for t in transactions:
            await self.db.refresh(t)
        
        return transactions
    
    async def update_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        data: TransactionUpdate,
    ) -> Optional[Transaction]:
        """
        Update an existing transaction.
        
        Args:
            transaction_id: Transaction UUID
            user_id: User UUID
            data: Fields to update
            
        Returns:
            Updated Transaction
        """
        transaction = await self.get_transaction(transaction_id, user_id)
        if not transaction:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # If category is being manually set, clear auto-categorization
        if "category_id" in update_data:
            transaction.is_auto_categorized = False
            transaction.categorization_confidence = None
        
        for field, value in update_data.items():
            setattr(transaction, field, value)
        
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction
    
    async def delete_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a transaction.
        
        Args:
            transaction_id: Transaction UUID
            user_id: User UUID
            
        Returns:
            True if deleted
        """
        transaction = await self.get_transaction(transaction_id, user_id)
        if not transaction:
            return False
        
        await self.db.delete(transaction)
        await self.db.flush()
        return True
    
    async def categorize_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        category_id: UUID,
    ) -> Optional[Transaction]:
        """
        Manually categorize a transaction.
        
        Args:
            transaction_id: Transaction UUID
            user_id: User UUID
            category_id: Category UUID
            
        Returns:
            Updated Transaction
        """
        transaction = await self.get_transaction(transaction_id, user_id)
        if not transaction:
            return None
        
        transaction.category_id = category_id
        transaction.is_auto_categorized = False
        transaction.categorization_confidence = None
        
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction
    
    async def _auto_categorize(
        self,
        description: str,
        merchant_name: Optional[str],
        amount: Decimal,
        user_id: UUID,
    ) -> Tuple[Optional[UUID], float]:
        """
        Auto-categorize transaction using ML.
        
        Args:
            description: Transaction description
            merchant_name: Merchant name
            amount: Transaction amount
            user_id: User UUID
            
        Returns:
            Tuple of (category_id, confidence)
        """
        # Get available categories for user
        result = await self.db.execute(
            select(Category).where(
                or_(
                    Category.user_id == user_id,
                    Category.is_system == True,
                )
            )
        )
        categories = result.scalars().all()
        
        if not categories:
            return None, 0.0
        
        # Use ML categorizer
        prediction = self.categorizer.predict(
            description=description,
            merchant_name=merchant_name,
            amount=float(amount),
            categories=categories,
        )
        
        return prediction
