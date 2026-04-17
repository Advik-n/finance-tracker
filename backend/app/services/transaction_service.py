"""
Transaction Service

Handles transaction CRUD operations and categorization.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.transaction import Transaction, TransactionSource, TransactionType
from app.models.category import Category
from app.schemas.transaction import (
    CategoryBrief,
    TransactionCreate,
    TransactionBulkCreateRequest,
    TransactionBulkCreateResponse,
    TransactionUpdate,
    TransactionFilter,
    TransactionResponse,
    TransactionSummary,
)
from app.ml.categorizer import TransactionCategorizer
from app.utils.helpers import generate_slug


class TransactionService:
    """
    Service class for transaction operations.
    
    Handles CRUD, filtering, and auto-categorization.
    """

    CATEGORY_ALIASES = {
        "clothes": "clothes-apparel",
        "clothing": "clothes-apparel",
        "apparel": "clothes-apparel",
        "gas": "petrol",
        "fuel": "petrol",
        "grocery": "groceries",
        "groceriesration": "groceries",
        "food": "food-dining",
        "utilities": "utilities",
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.categorizer = TransactionCategorizer()

    def _normalize_category_key(self, name: str) -> str:
        slug = generate_slug(name)
        return self.CATEGORY_ALIASES.get(slug, slug)

    def _build_category_lookup(self, categories: List[Category]) -> dict[str, Category]:
        lookup: dict[str, Category] = {}
        for category in categories:
            lookup[generate_slug(category.name)] = category
            lookup[category.name.lower()] = category
        return lookup

    def _resolve_category_id(
        self,
        categories: List[Category],
        category_name: Optional[str],
        subcategory_name: Optional[str],
    ) -> Optional[UUID]:
        lookup = self._build_category_lookup(categories)
        for name in (subcategory_name, category_name):
            if not name:
                continue
            key = self._normalize_category_key(name)
            if key in lookup:
                return lookup[key].id
            name_key = name.lower()
            if name_key in lookup:
                return lookup[name_key].id
        return None
    
    async def list_transactions(
        self,
        user_id: UUID,
        filters: TransactionFilter,
        page: int = 1,
        page_size: int = 50,
        limit: int = None,  # deprecated, use page_size
    ) -> Tuple[List[Transaction], int]:
        """
        List transactions with filtering and pagination.
        
        Args:
            user_id: User UUID
            filters: Filter parameters
            page: Page number
            page_size: Items per page (replaces limit)
            limit: Deprecated, use page_size
            
        Returns:
            Tuple of (transactions list, total count)
        """
        # Support both limit and page_size for backwards compatibility
        items_per_page = page_size if limit is None else limit
        
        # Base query
        query = select(Transaction).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.is_deleted == False,  # noqa: E712
            )
        )
        count_query = select(func.count()).select_from(Transaction).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.is_deleted == False,  # noqa: E712
            )
        )
        
        # Apply filters
        if filters.category_id:
            query = query.where(Transaction.category_id == filters.category_id)
            count_query = count_query.where(Transaction.category_id == filters.category_id)
        if filters.category_ids:
            query = query.where(Transaction.category_id.in_(filters.category_ids))
            count_query = count_query.where(Transaction.category_id.in_(filters.category_ids))
        
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
        if filters.source:
            query = query.where(Transaction.source == filters.source)
            count_query = count_query.where(Transaction.source == filters.source)
        if filters.is_recurring is not None:
            query = query.where(Transaction.is_recurring == filters.is_recurring)
            count_query = count_query.where(Transaction.is_recurring == filters.is_recurring)
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        offset = (page - 1) * items_per_page
        query = (
            query
            .options(joinedload(Transaction.category))
            .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
            .offset(offset)
            .limit(items_per_page)
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
                    Transaction.is_deleted == False,  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create_transaction(
        self,
        user_id: UUID,
        data: TransactionCreate,
        source: TransactionSource = TransactionSource.MANUAL,
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
            transaction_date=data.transaction_date,
            description=data.description,
            merchant_name=data.merchant_name,
            transaction_type=data.transaction_type,
            notes=data.notes,
            tags=data.tags,
            is_recurring=data.is_recurring,
            source=source,
        )
        
        # Auto-categorize if no category provided
        if data.category_id:
            transaction.category_id = data.category_id
        else:
            category_id, confidence = await self._auto_categorize(
                description=data.description,
                merchant_name=data.merchant_name,
                amount=data.amount,
                transaction_type=data.transaction_type,
                user_id=user_id,
                transaction_date=data.transaction_date,
            )
            if category_id:
                transaction.category_id = category_id
                transaction.is_auto_categorized = True
                transaction.confidence_score = float(confidence)
        
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
        source: TransactionSource = TransactionSource.MANUAL,
        upload_batch_id: UUID | None = None,
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
                transaction_date=item.transaction_date,
                description=item.description,
                merchant_name=item.merchant_name,
                transaction_type=item.transaction_type,
                notes=item.notes,
                tags=item.tags,
                is_recurring=item.is_recurring,
                category_id=item.category_id,
                source=source,
                upload_batch_id=upload_batch_id,
            )
            
            # Auto-categorize if no category
            if not item.category_id:
                category_id, confidence = await self._auto_categorize(
                    description=item.description,
                    merchant_name=item.merchant_name,
                    amount=item.amount,
                    transaction_type=item.transaction_type,
                    user_id=user_id,
                    transaction_date=item.transaction_date,
                )
                if category_id:
                    transaction.category_id = category_id
                    transaction.is_auto_categorized = True
                    transaction.confidence_score = float(confidence)
            
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
            transaction.confidence_score = None
        
        for field, value in update_data.items():
            setattr(transaction, field, value)
        
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction
    
    async def delete_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        hard_delete: bool = False,
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
        
        if hard_delete:
            await self.db.delete(transaction)
        else:
            transaction.is_deleted = True
            transaction.deleted_at = datetime.utcnow()
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
        transaction.confidence_score = None
        
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction
    
    async def _auto_categorize(
        self,
        description: str,
        merchant_name: Optional[str],
        amount: Decimal,
        transaction_type: TransactionType,
        user_id: UUID,
        transaction_date: Optional[datetime] = None,
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
        
        # Use new categorizer pipeline
        from app.ml.categorizer import TransactionInput

        transaction = TransactionInput(
            description=f"{description} {merchant_name or ''}".strip(),
            amount=float(amount),
            transaction_type=transaction_type.value.lower(),
            date=transaction_date or datetime.utcnow(),
        )
        result = self.categorizer.categorize(transaction)
        category_id = self._resolve_category_id(
            categories=categories,
            category_name=result.category,
            subcategory_name=result.subcategory,
        )

        if category_id:
            return category_id, result.confidence

        # Fallback to legacy matching for custom categories
        return self.categorizer.predict(
            description=description,
            merchant_name=merchant_name,
            amount=float(amount),
            categories=categories,
        )

    def _to_response(self, transaction: Transaction) -> TransactionResponse:
        category = None
        if transaction.category:
            category = CategoryBrief(
                id=transaction.category.id,
                name=transaction.category.name,
                icon=transaction.category.icon,
                color=transaction.category.color,
            )

        return TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            amount=transaction.amount,
            transaction_type=transaction.transaction_type,
            category=category,
            merchant_name=transaction.merchant_name,
            merchant_category=transaction.merchant_category,
            description=transaction.description,
            transaction_date=transaction.transaction_date,
            source=transaction.source,
            bank_name=transaction.bank_name,
            account_last_4=transaction.account_last_4,
            confidence_score=transaction.confidence_score,
            is_auto_categorized=transaction.is_auto_categorized,
            is_recurring=transaction.is_recurring,
            recurring_pattern=transaction.recurring_pattern,
            tags=transaction.tags or [],
            notes=transaction.notes,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
        )

    async def search_transactions(
        self,
        user_id: UUID,
        query: str,
        limit: int = 20,
    ) -> List[Transaction]:
        search_term = f"%{query}%"
        result = await self.db.execute(
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.is_deleted == False,  # noqa: E712
                    or_(
                        Transaction.description.ilike(search_term),
                        Transaction.merchant_name.ilike(search_term),
                        Transaction.notes.ilike(search_term),
                    ),
                )
            )
            .order_by(Transaction.transaction_date.desc())
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def get_summary(
        self,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> TransactionSummary:
        today = date.today()
        if not end_date:
            end_date = today
        if not start_date:
            start_date = date(today.year, today.month, 1)

        result = await self.db.execute(
            select(
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.CREDIT, Transaction.amount),
                        else_=Decimal("0"),
                    )
                ).label("total_income"),
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.DEBIT, Transaction.amount),
                        else_=Decimal("0"),
                    )
                ).label("total_expense"),
                func.count().label("transaction_count"),
                func.max(
                    case(
                        (Transaction.transaction_type == TransactionType.DEBIT, Transaction.amount),
                        else_=None,
                    )
                ).label("largest_expense"),
                func.max(
                    case(
                        (Transaction.transaction_type == TransactionType.CREDIT, Transaction.amount),
                        else_=None,
                    )
                ).label("largest_income"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                    Transaction.is_deleted == False,  # noqa: E712
                )
            )
        )
        row = result.first()

        total_income = row.total_income or Decimal("0")
        total_expense = row.total_expense or Decimal("0")
        transaction_count = row.transaction_count or 0
        avg = Decimal("0")
        if transaction_count:
            avg = (total_income + total_expense) / transaction_count

        return TransactionSummary(
            total_income=total_income,
            total_expense=total_expense,
            net_amount=total_income - total_expense,
            transaction_count=transaction_count,
            avg_transaction_amount=avg,
            largest_expense=row.largest_expense,
            largest_income=row.largest_income,
        )

    async def bulk_create_transactions(
        self,
        user_id: UUID,
        data: TransactionBulkCreateRequest,
    ) -> TransactionBulkCreateResponse:
        created: List[Transaction] = []
        errors: List[dict] = []

        for index, item in enumerate(data.transactions):
            try:
                transaction = Transaction(
                    user_id=user_id,
                    amount=item.amount,
                    transaction_date=item.transaction_date,
                    description=item.description,
                    merchant_name=item.merchant_name,
                    transaction_type=item.transaction_type,
                    notes=item.notes,
                    tags=item.tags,
                    is_recurring=item.is_recurring,
                    category_id=item.category_id,
                    source=data.source,
                    upload_batch_id=data.upload_batch_id,
                )

                if not item.category_id:
                    category_id, confidence = await self._auto_categorize(
                        description=item.description,
                        merchant_name=item.merchant_name,
                        amount=item.amount,
                        transaction_type=item.transaction_type,
                        user_id=user_id,
                        transaction_date=item.transaction_date,
                    )
                    if category_id:
                        transaction.category_id = category_id
                        transaction.is_auto_categorized = True
                        transaction.confidence_score = float(confidence)

                self.db.add(transaction)
                created.append(transaction)
            except Exception as exc:
                errors.append({"index": index, "error": str(exc)})

        await self.db.flush()

        for transaction in created:
            await self.db.refresh(transaction)

        return TransactionBulkCreateResponse(
            created_count=len(created),
            failed_count=len(errors),
            duplicate_count=0,
            transactions=[self._to_response(t) for t in created],
            errors=errors or None,
        )
