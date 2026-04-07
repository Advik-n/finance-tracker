"""
Universal Statement Parser

Unified parser that handles any supported file format with automatic
detection and routing to appropriate format-specific parsers.
"""

import logging
import mimetypes
from typing import List, Optional, Dict, Any, Tuple
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_parser import (
    BaseParser,
    ParsedTransaction,
    ParserResult,
    TransactionType,
    ParserError,
    UnsupportedFormatError,
)
from .pdf_parser import PDFStatementParser
from .csv_parser import CSVStatementParser
from .excel_parser import ExcelStatementParser
from .cleaners import DataCleaner, TransactionCategorizer

logger = logging.getLogger(__name__)


class UniversalParser:
    """
    Unified parser that handles any supported format.
    
    Features:
    - Auto-detect file type from content and extension
    - Route to appropriate format-specific parser
    - Batch processing with parallel execution
    - Deduplication across files
    - Comprehensive error handling
    """
    
    VERSION = "1.0.0"
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        'pdf': PDFStatementParser,
        'csv': CSVStatementParser,
        'txt': CSVStatementParser,
        'xlsx': ExcelStatementParser,
        'xls': ExcelStatementParser,
        'xlsm': ExcelStatementParser,
    }
    
    # MIME type mappings
    MIME_MAPPINGS = {
        'application/pdf': PDFStatementParser,
        'text/csv': CSVStatementParser,
        'text/plain': CSVStatementParser,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ExcelStatementParser,
        'application/vnd.ms-excel': ExcelStatementParser,
    }
    
    # Magic bytes for file type detection
    MAGIC_BYTES = {
        b'%PDF': PDFStatementParser,
        b'PK': ExcelStatementParser,  # XLSX is a ZIP file
        b'\xd0\xcf\x11\xe0': ExcelStatementParser,  # XLS (OLE format)
    }
    
    def __init__(
        self,
        enable_ocr: bool = True,
        max_workers: int = 4,
        deduplicate: bool = True
    ):
        """
        Initialize the universal parser.
        
        Args:
            enable_ocr: Enable OCR for scanned PDFs
            max_workers: Max parallel workers for batch processing
            deduplicate: Remove duplicate transactions across files
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.enable_ocr = enable_ocr
        self.max_workers = max_workers
        self.deduplicate = deduplicate
        
        # Initialize parsers
        self.parsers = {
            'pdf': PDFStatementParser(enable_ocr=enable_ocr),
            'csv': CSVStatementParser(),
            'excel': ExcelStatementParser(),
        }
        
        self.cleaner = DataCleaner()
        self.categorizer = TransactionCategorizer()
    
    def parse(
        self,
        file_content: bytes,
        filename: str,
        file_type: str = None
    ) -> ParserResult:
        """
        Parse a bank statement file with automatic format detection.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_type: Optional explicit file type (pdf, csv, xlsx, etc.)
            
        Returns:
            ParserResult with parsed transactions
        """
        start_time = time.time()
        
        try:
            # Detect or validate file type
            if file_type:
                parser_key = self._normalize_file_type(file_type)
            else:
                parser_key = self._detect_file_type(file_content, filename)
            
            if not parser_key:
                result = ParserResult(source_file=filename)
                result.add_error(f"Unsupported file format: {filename}")
                return result
            
            # Get appropriate parser
            parser = self.parsers.get(parser_key)
            if not parser:
                result = ParserResult(source_file=filename)
                result.add_error(f"No parser available for type: {parser_key}")
                return result
            
            # Validate file can be parsed
            if not parser.can_parse(file_content, filename):
                result = ParserResult(source_file=filename)
                result.add_error(f"Parser cannot handle file: {filename}")
                return result
            
            # Parse the file
            result = parser.parse(file_content, filename)
            
            # Post-process results
            self._post_process(result)
            
            self.logger.info(
                f"Parsed {result.transaction_count} transactions from {filename} "
                f"in {result.parsing_time_ms:.0f}ms"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Universal parser error: {e}", exc_info=True)
            result = ParserResult(source_file=filename)
            result.add_error(f"Parsing failed: {str(e)}")
            result.parsing_time_ms = (time.time() - start_time) * 1000
            return result
    
    def parse_multiple(
        self,
        files: List[Tuple[bytes, str]],
        parallel: bool = True
    ) -> List[ParserResult]:
        """
        Parse multiple files in batch.
        
        Args:
            files: List of (file_content, filename) tuples
            parallel: Use parallel processing
            
        Returns:
            List of ParserResult objects
        """
        if not files:
            return []
        
        self.logger.info(f"Batch parsing {len(files)} files")
        
        if parallel and len(files) > 1:
            results = self._parse_parallel(files)
        else:
            results = self._parse_sequential(files)
        
        # Deduplicate across all files if enabled
        if self.deduplicate and len(results) > 1:
            results = self._deduplicate_across_results(results)
        
        return results
    
    def _parse_sequential(self, files: List[Tuple[bytes, str]]) -> List[ParserResult]:
        """Parse files sequentially."""
        results = []
        for file_content, filename in files:
            result = self.parse(file_content, filename)
            results.append(result)
        return results
    
    def _parse_parallel(self, files: List[Tuple[bytes, str]]) -> List[ParserResult]:
        """Parse files in parallel using ThreadPoolExecutor."""
        results = [None] * len(files)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(self.parse, content, name): idx
                for idx, (content, name) in enumerate(files)
            }
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    self.logger.error(f"Parallel parsing error: {e}")
                    result = ParserResult(source_file=files[idx][1])
                    result.add_error(f"Parsing failed: {str(e)}")
                    results[idx] = result
        
        return results
    
    def _detect_file_type(self, file_content: bytes, filename: str) -> Optional[str]:
        """
        Detect file type from content and filename.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            Parser key (pdf, csv, excel) or None
        """
        # Try magic bytes first (most reliable)
        for magic, parser_class in self.MAGIC_BYTES.items():
            if file_content.startswith(magic):
                if parser_class == PDFStatementParser:
                    return 'pdf'
                elif parser_class == ExcelStatementParser:
                    return 'excel'
        
        # Try MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type in self.MIME_MAPPINGS:
            parser_class = self.MIME_MAPPINGS[mime_type]
            if parser_class == PDFStatementParser:
                return 'pdf'
            elif parser_class == CSVStatementParser:
                return 'csv'
            elif parser_class == ExcelStatementParser:
                return 'excel'
        
        # Try file extension
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext in ['pdf']:
            return 'pdf'
        elif ext in ['csv', 'txt']:
            return 'csv'
        elif ext in ['xlsx', 'xls', 'xlsm']:
            return 'excel'
        
        # Try to detect CSV by content
        if self._looks_like_csv(file_content):
            return 'csv'
        
        return None
    
    def _normalize_file_type(self, file_type: str) -> Optional[str]:
        """Normalize file type string to parser key."""
        file_type = file_type.lower().strip()
        
        if file_type in ['pdf']:
            return 'pdf'
        elif file_type in ['csv', 'txt', 'text']:
            return 'csv'
        elif file_type in ['xlsx', 'xls', 'xlsm', 'excel']:
            return 'excel'
        
        return None
    
    def _looks_like_csv(self, content: bytes) -> bool:
        """Check if content looks like CSV data."""
        try:
            # Try to decode as text
            text = content[:2000].decode('utf-8', errors='ignore')
            
            # Check for common CSV patterns
            lines = text.split('\n')[:5]
            if not lines:
                return False
            
            # Check if lines have consistent delimiter counts
            delimiters = [',', ';', '\t', '|']
            for delim in delimiters:
                counts = [line.count(delim) for line in lines if line.strip()]
                if counts and all(c == counts[0] for c in counts) and counts[0] >= 2:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _post_process(self, result: ParserResult) -> None:
        """Post-process parsing results."""
        # Categorize uncategorized transactions
        for txn in result.transactions:
            if not txn.category:
                txn.category = self.categorizer.categorize(txn.description)
        
        # Sort by date
        result.transactions.sort(key=lambda t: t.date)
    
    def _deduplicate_across_results(
        self,
        results: List[ParserResult]
    ) -> List[ParserResult]:
        """Remove duplicates across multiple parsing results."""
        # Collect all transactions with their source
        all_txns = []
        for result in results:
            for txn in result.transactions:
                all_txns.append((txn, result))
        
        # Find and mark duplicates
        duplicates_found = 0
        seen_hashes = set()
        
        for txn, result in all_txns:
            # Create a hash for the transaction
            txn_hash = self._transaction_hash(txn)
            
            if txn_hash in seen_hashes:
                # This is a duplicate - remove from result
                if txn in result.transactions:
                    result.transactions.remove(txn)
                    duplicates_found += 1
            else:
                seen_hashes.add(txn_hash)
        
        if duplicates_found > 0:
            self.logger.info(
                f"Removed {duplicates_found} duplicate transactions across files"
            )
            # Add warning to first result
            results[0].add_warning(
                f"Removed {duplicates_found} duplicate transactions across files"
            )
        
        return results
    
    def _transaction_hash(self, txn: ParsedTransaction) -> str:
        """Create a hash for transaction deduplication."""
        # Create a string representation of key fields
        key = f"{txn.date}|{txn.amount:.2f}|{txn.transaction_type.value}|{txn.description[:50]}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get information about supported file formats."""
        return {
            'pdf': {
                'extensions': ['.pdf'],
                'description': 'PDF bank statements (text and scanned)',
                'ocr_support': self.enable_ocr,
            },
            'csv': {
                'extensions': ['.csv', '.txt'],
                'description': 'CSV exports from banks and payment apps',
            },
            'excel': {
                'extensions': ['.xlsx', '.xls', '.xlsm'],
                'description': 'Excel exports from bank portals',
            },
        }
    
    def validate_file(
        self,
        file_content: bytes,
        filename: str
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate if a file can be parsed.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            Tuple of (is_valid, detected_type, list_of_issues)
        """
        issues = []
        
        # Check file size
        if len(file_content) == 0:
            issues.append("File is empty")
            return False, None, issues
        
        if len(file_content) > 50 * 1024 * 1024:  # 50MB limit
            issues.append("File exceeds maximum size (50MB)")
            return False, None, issues
        
        # Detect file type
        file_type = self._detect_file_type(file_content, filename)
        
        if not file_type:
            issues.append("Unsupported file format")
            return False, None, issues
        
        # Get parser and validate
        parser = self.parsers.get(file_type)
        if parser and not parser.can_parse(file_content, filename):
            issues.append(f"File appears to be corrupted or malformed")
            return False, file_type, issues
        
        return True, file_type, issues


class ParserFactory:
    """
    Factory for creating parser instances.
    """
    
    _parsers = {
        'pdf': PDFStatementParser,
        'csv': CSVStatementParser,
        'excel': ExcelStatementParser,
    }
    
    @classmethod
    def create(cls, parser_type: str, **kwargs) -> BaseParser:
        """
        Create a parser instance.
        
        Args:
            parser_type: Type of parser (pdf, csv, excel)
            **kwargs: Parser-specific configuration
            
        Returns:
            Parser instance
        """
        parser_class = cls._parsers.get(parser_type.lower())
        if not parser_class:
            raise ValueError(f"Unknown parser type: {parser_type}")
        
        return parser_class(**kwargs)
    
    @classmethod
    def get_available_parsers(cls) -> List[str]:
        """Get list of available parser types."""
        return list(cls._parsers.keys())


def parse_statement(
    file_content: bytes,
    filename: str,
    file_type: str = None,
    enable_ocr: bool = True
) -> ParserResult:
    """
    Convenience function to parse a bank statement.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        file_type: Optional explicit file type
        enable_ocr: Enable OCR for scanned PDFs
        
    Returns:
        ParserResult with parsed transactions
    """
    parser = UniversalParser(enable_ocr=enable_ocr)
    return parser.parse(file_content, filename, file_type)


def parse_statements(
    files: List[Tuple[bytes, str]],
    enable_ocr: bool = True,
    parallel: bool = True
) -> List[ParserResult]:
    """
    Convenience function to parse multiple bank statements.
    
    Args:
        files: List of (file_content, filename) tuples
        enable_ocr: Enable OCR for scanned PDFs
        parallel: Use parallel processing
        
    Returns:
        List of ParserResult objects
    """
    parser = UniversalParser(enable_ocr=enable_ocr)
    return parser.parse_multiple(files, parallel=parallel)
