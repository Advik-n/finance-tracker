"""
Bank Statement Parsers Package

Multi-format parsers for extracting transactions from bank statements.
Supports PDF, CSV, and Excel files with automatic format detection.
"""

from .base_parser import (
    BaseParser,
    ParsedTransaction,
    ParserResult,
    TransactionType,
    ParserError,
    UnsupportedFormatError,
    MalformedDataError,
    BankNotRecognizedError,
    BANK_PATTERNS,
    UPI_APP_PATTERNS,
)

from .cleaners import (
    DataCleaner,
    TransactionCategorizer,
)

from .pdf_parser import PDFStatementParser
from .csv_parser import CSVStatementParser
from .excel_parser import ExcelStatementParser, ExcelParser
from .ocr_parser import OCRParser, check_ocr_dependencies
from .universal_parser import (
    UniversalParser,
    ParserFactory,
    parse_statement,
    parse_statements,
)


__all__ = [
    # Base classes and types
    'BaseParser',
    'ParsedTransaction',
    'ParserResult',
    'TransactionType',
    
    # Exceptions
    'ParserError',
    'UnsupportedFormatError',
    'MalformedDataError',
    'BankNotRecognizedError',
    
    # Constants
    'BANK_PATTERNS',
    'UPI_APP_PATTERNS',
    
    # Utilities
    'DataCleaner',
    'TransactionCategorizer',
    
    # Parsers
    'PDFStatementParser',
    'CSVStatementParser',
    'ExcelStatementParser',
    'ExcelParser',  # Backward compatibility
    'OCRParser',
    'UniversalParser',
    
    # Factory
    'ParserFactory',
    
    # Convenience functions
    'parse_statement',
    'parse_statements',
    'check_ocr_dependencies',
]


__version__ = '1.0.0'
