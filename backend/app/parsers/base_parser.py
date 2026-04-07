"""
Base Parser Module for Bank Statement Parsing

Provides abstract base classes and data models for all statement parsers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import logging

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class TransactionType(str, Enum):
    """Transaction type enumeration"""
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    UNKNOWN = "UNKNOWN"


class ParsedTransaction(BaseModel):
    """
    Represents a single parsed transaction from a bank statement.
    
    Attributes:
        date: Transaction date in ISO format (YYYY-MM-DD)
        description: Transaction description/narration
        amount: Absolute transaction amount (always positive)
        transaction_type: CREDIT or DEBIT
        balance: Account balance after transaction (if available)
        reference: Transaction reference number (if available)
        raw_text: Original raw text from which this was parsed
        confidence: Confidence score of parsing accuracy (0.0 to 1.0)
        category: Auto-detected category (if available)
        metadata: Additional bank-specific metadata
    """
    date: str
    description: str
    amount: float
    transaction_type: TransactionType = TransactionType.UNKNOWN
    balance: Optional[float] = None
    reference: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    category: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('amount')
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        """Ensure amount is always positive"""
        return abs(v)
    
    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in correct format"""
        try:
            # Try parsing ISO format
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            # Try other common formats and convert
            for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%m/%d/%Y"]:
                try:
                    dt = datetime.strptime(v, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            raise ValueError(f"Invalid date format: {v}")
    
    @field_validator('description')
    @classmethod
    def clean_description(cls, v: str) -> str:
        """Clean up description whitespace"""
        if v:
            return ' '.join(v.split())
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "date": self.date,
            "description": self.description,
            "amount": self.amount,
            "transaction_type": self.transaction_type.value,
            "balance": self.balance,
            "reference": self.reference,
            "confidence": self.confidence,
            "category": self.category,
            "metadata": self.metadata,
        }


class ParserResult(BaseModel):
    """
    Result of parsing a bank statement.
    
    Attributes:
        transactions: List of parsed transactions
        bank_name: Detected bank name
        account_number_masked: Masked account number (last 4 digits)
        account_holder: Account holder name (if detected)
        statement_period: Statement period string
        opening_balance: Opening balance (if detected)
        closing_balance: Closing balance (if detected)
        currency: Currency code (default INR)
        errors: List of fatal parsing errors
        warnings: List of non-fatal warnings
        metadata: Additional parser-specific metadata
        parsing_time_ms: Time taken to parse in milliseconds
        source_file: Original filename
        parser_version: Version of parser used
    """
    transactions: List[ParsedTransaction] = Field(default_factory=list)
    bank_name: Optional[str] = None
    account_number_masked: Optional[str] = None
    account_holder: Optional[str] = None
    statement_period: Optional[str] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    currency: str = "INR"
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parsing_time_ms: Optional[float] = None
    source_file: Optional[str] = None
    parser_version: str = "1.0.0"
    
    @property
    def is_successful(self) -> bool:
        """Check if parsing was successful (has transactions and no fatal errors)"""
        return len(self.transactions) > 0 and len(self.errors) == 0
    
    @property
    def total_credits(self) -> float:
        """Sum of all credit transactions"""
        return sum(
            t.amount for t in self.transactions 
            if t.transaction_type == TransactionType.CREDIT
        )
    
    @property
    def total_debits(self) -> float:
        """Sum of all debit transactions"""
        return sum(
            t.amount for t in self.transactions 
            if t.transaction_type == TransactionType.DEBIT
        )
    
    @property
    def transaction_count(self) -> int:
        """Total number of transactions"""
        return len(self.transactions)
    
    def add_error(self, error: str) -> None:
        """Add a fatal error"""
        logger.error(f"Parser error: {error}")
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a non-fatal warning"""
        logger.warning(f"Parser warning: {warning}")
        self.warnings.append(warning)
    
    def merge(self, other: 'ParserResult') -> 'ParserResult':
        """Merge another ParserResult into this one"""
        self.transactions.extend(other.transactions)
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self

    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary of parsing results"""
        return {
            "bank_name": self.bank_name,
            "account_number_masked": self.account_number_masked,
            "statement_period": self.statement_period,
            "transaction_count": self.transaction_count,
            "total_credits": self.total_credits,
            "total_debits": self.total_debits,
            "opening_balance": self.opening_balance,
            "closing_balance": self.closing_balance,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "parsing_time_ms": self.parsing_time_ms,
        }


class BaseParser(ABC):
    """
    Abstract base class for all statement parsers.
    
    All parser implementations must inherit from this class and implement
    the parse() and can_parse() methods.
    """
    
    # Parser metadata
    PARSER_NAME: str = "BaseParser"
    PARSER_VERSION: str = "1.0.0"
    SUPPORTED_FORMATS: List[str] = []
    
    def __init__(self):
        """Initialize the parser"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    @abstractmethod
    def parse(self, file_content: bytes, filename: str) -> ParserResult:
        """
        Parse a bank statement file.
        
        Args:
            file_content: Raw bytes of the file
            filename: Original filename (used for format detection)
            
        Returns:
            ParserResult containing parsed transactions and metadata
        """
        pass
    
    @abstractmethod
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """
        Check if this parser can handle the given file.
        
        Args:
            file_content: Raw bytes of the file
            filename: Original filename
            
        Returns:
            True if this parser can handle the file, False otherwise
        """
        pass
    
    def get_parser_info(self) -> Dict[str, Any]:
        """Get parser metadata"""
        return {
            "name": self.PARSER_NAME,
            "version": self.PARSER_VERSION,
            "supported_formats": self.SUPPORTED_FORMATS,
        }
    
    def _create_result(self, filename: str) -> ParserResult:
        """Create an empty ParserResult with metadata"""
        return ParserResult(
            source_file=filename,
            parser_version=self.PARSER_VERSION,
        )
    
    def _create_transaction(
        self,
        date: str,
        description: str,
        amount: float,
        transaction_type: TransactionType,
        **kwargs
    ) -> Optional[ParsedTransaction]:
        """
        Safely create a ParsedTransaction with validation.
        
        Returns None if creation fails.
        """
        try:
            return ParsedTransaction(
                date=date,
                description=description,
                amount=amount,
                transaction_type=transaction_type,
                **kwargs
            )
        except Exception as e:
            self.logger.warning(f"Failed to create transaction: {e}")
            return None


class ParserError(Exception):
    """Base exception for parser errors"""
    pass


class UnsupportedFormatError(ParserError):
    """Raised when the file format is not supported"""
    pass


class MalformedDataError(ParserError):
    """Raised when the data is malformed or corrupted"""
    pass


class BankNotRecognizedError(ParserError):
    """Raised when the bank format cannot be recognized"""
    pass


# Bank identifier patterns for detection
BANK_PATTERNS = {
    "hdfc": [
        r"HDFC\s*BANK",
        r"hdfc\s*bank",
        r"HDFCBANK",
    ],
    "sbi": [
        r"STATE\s*BANK\s*OF\s*INDIA",
        r"SBI",
        r"SBIN",
    ],
    "icici": [
        r"ICICI\s*BANK",
        r"ICICIBANK",
    ],
    "axis": [
        r"AXIS\s*BANK",
        r"AXISBANK",
    ],
    "kotak": [
        r"KOTAK\s*MAHINDRA",
        r"KOTAK\s*BANK",
        r"KOTAKBANK",
    ],
    "idfc": [
        r"IDFC\s*FIRST",
        r"IDFC\s*BANK",
        r"IDFCFIRST",
    ],
    "yes": [
        r"YES\s*BANK",
        r"YESBANK",
    ],
    "scb": [
        r"STANDARD\s*CHARTERED",
        r"SCB",
    ],
    "citi": [
        r"CITIBANK",
        r"CITI\s*BANK",
    ],
    "pnb": [
        r"PUNJAB\s*NATIONAL\s*BANK",
        r"PNB",
    ],
    "bob": [
        r"BANK\s*OF\s*BARODA",
        r"BOB",
    ],
    "canara": [
        r"CANARA\s*BANK",
        r"CANARABANK",
    ],
    "union": [
        r"UNION\s*BANK",
        r"UNIONBANK",
    ],
    "indian": [
        r"INDIAN\s*BANK",
        r"INDIANBANK",
    ],
    "indusind": [
        r"INDUSIND\s*BANK",
        r"INDUSINDBANK",
    ],
    "federal": [
        r"FEDERAL\s*BANK",
        r"FEDERALBANK",
    ],
    "rbl": [
        r"RBL\s*BANK",
        r"RATNAKAR\s*BANK",
    ],
    "bandhan": [
        r"BANDHAN\s*BANK",
        r"BANDHANBANK",
    ],
}

# UPI app patterns
UPI_APP_PATTERNS = {
    "gpay": [
        r"GOOGLE\s*PAY",
        r"GPAY",
    ],
    "phonepe": [
        r"PHONEPE",
        r"PHONE\s*PE",
    ],
    "paytm": [
        r"PAYTM",
        r"PAY\s*TM",
    ],
    "amazonpay": [
        r"AMAZON\s*PAY",
        r"AMAZONPAY",
    ],
    "bhim": [
        r"BHIM",
    ],
    "mobikwik": [
        r"MOBIKWIK",
    ],
}
