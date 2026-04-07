"""
PDF Statement Parser for Bank Statements

Parses bank statement PDFs from major Indian banks using text extraction
and OCR fallback for scanned documents.
"""

import io
import re
import logging
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime
import time

from .base_parser import (
    BaseParser,
    ParsedTransaction,
    ParserResult,
    TransactionType,
    BANK_PATTERNS,
    ParserError,
    UnsupportedFormatError,
    MalformedDataError,
    BankNotRecognizedError,
)
from .cleaners import DataCleaner, TransactionCategorizer

logger = logging.getLogger(__name__)


class PDFStatementParser(BaseParser):
    """
    Parse bank statement PDFs from major Indian banks.
    
    Supports:
    - HDFC Bank
    - SBI (State Bank of India)
    - ICICI Bank
    - Axis Bank
    - Kotak Mahindra Bank
    - IDFC First Bank
    - Yes Bank
    - Standard Chartered
    - Citibank
    - PNB (Punjab National Bank)
    - Bank of Baroda
    - Canara Bank
    - IndusInd Bank
    - Federal Bank
    - RBL Bank
    """
    
    PARSER_NAME = "PDFStatementParser"
    PARSER_VERSION = "1.0.0"
    SUPPORTED_FORMATS = [".pdf"]
    
    def __init__(self, enable_ocr: bool = True):
        """
        Initialize the PDF parser.
        
        Args:
            enable_ocr: Whether to use OCR for scanned PDFs
        """
        super().__init__()
        self.enable_ocr = enable_ocr
        self.cleaner = DataCleaner()
        self.categorizer = TransactionCategorizer()
        
        # Bank-specific parsers
        self._bank_parsers = {
            'hdfc': self._parse_hdfc_format,
            'sbi': self._parse_sbi_format,
            'icici': self._parse_icici_format,
            'axis': self._parse_axis_format,
            'kotak': self._parse_kotak_format,
            'idfc': self._parse_idfc_format,
            'yes': self._parse_yes_format,
            'scb': self._parse_scb_format,
            'citi': self._parse_citi_format,
            'pnb': self._parse_pnb_format,
            'bob': self._parse_bob_format,
            'canara': self._parse_canara_format,
            'indusind': self._parse_indusind_format,
            'federal': self._parse_federal_format,
            'rbl': self._parse_rbl_format,
        }
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """Check if this parser can handle the file."""
        if not filename.lower().endswith('.pdf'):
            return False
        
        # Check PDF magic bytes
        if not file_content.startswith(b'%PDF'):
            return False
        
        return True
    
    def parse(self, file_content: bytes, filename: str) -> ParserResult:
        """
        Parse a bank statement PDF.
        
        Args:
            file_content: Raw PDF bytes
            filename: Original filename
            
        Returns:
            ParserResult with parsed transactions
        """
        start_time = time.time()
        result = self._create_result(filename)
        
        try:
            # Validate PDF
            if not self.can_parse(file_content, filename):
                result.add_error("Invalid PDF file or unsupported format")
                return result
            
            # Extract text from PDF
            text = self._extract_text(file_content)
            
            # If text extraction yields little content, try OCR
            if len(text.strip()) < 100 and self.enable_ocr:
                self.logger.info("Text extraction yielded little content, attempting OCR")
                result.add_warning("Using OCR for text extraction (scanned PDF)")
                text = self._extract_with_ocr(file_content)
            
            if not text or len(text.strip()) < 50:
                result.add_error("Could not extract text from PDF")
                return result
            
            # Detect bank
            bank_name = self._detect_bank(text)
            result.bank_name = self.cleaner.normalize_bank_name(bank_name)
            
            if not bank_name:
                result.add_warning("Could not identify bank, using generic parser")
                bank_name = 'generic'
            
            self.logger.info(f"Detected bank: {bank_name}")
            
            # Extract account info
            self._extract_account_info(text, result)
            
            # Parse transactions using bank-specific parser
            parser_func = self._bank_parsers.get(bank_name.lower(), self._parse_generic_format)
            transactions = parser_func(text)
            
            if not transactions:
                result.add_warning("No transactions found, trying generic parser")
                transactions = self._parse_generic_format(text)
            
            # Clean and validate transactions
            for txn in transactions:
                if txn:
                    # Categorize
                    if not txn.category:
                        txn.category = self.categorizer.categorize(txn.description)
                    result.transactions.append(txn)
            
            # Remove duplicates
            unique_txns, duplicates = self.cleaner.remove_duplicates(result.transactions)
            if duplicates:
                result.add_warning(f"Removed {len(duplicates)} duplicate transactions")
                result.transactions = unique_txns
            
            result.parsing_time_ms = (time.time() - start_time) * 1000
            
            self.logger.info(
                f"Parsed {len(result.transactions)} transactions from {filename}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"PDF parsing error: {e}", exc_info=True)
            result.add_error(f"PDF parsing failed: {str(e)}")
            result.parsing_time_ms = (time.time() - start_time) * 1000
            return result
    
    def _extract_text(self, file_content: bytes) -> str:
        """Extract text from PDF using PyPDF2."""
        try:
            import PyPDF2
            
            pdf_file = io.BytesIO(file_content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            return '\n'.join(text_parts)
            
        except ImportError:
            self.logger.warning("PyPDF2 not installed, trying pdfplumber")
            return self._extract_text_pdfplumber(file_content)
        except Exception as e:
            self.logger.warning(f"PyPDF2 extraction failed: {e}")
            return self._extract_text_pdfplumber(file_content)
    
    def _extract_text_pdfplumber(self, file_content: bytes) -> str:
        """Extract text using pdfplumber (better for tables)."""
        try:
            import pdfplumber
            
            pdf_file = io.BytesIO(file_content)
            text_parts = []
            
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    # Try table extraction first
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            for row in table:
                                if row:
                                    text_parts.append('\t'.join(str(cell or '') for cell in row))
                    else:
                        # Fall back to text extraction
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
            
            return '\n'.join(text_parts)
            
        except ImportError:
            self.logger.error("Neither PyPDF2 nor pdfplumber installed")
            raise ParserError("PDF parsing library not available")
        except Exception as e:
            self.logger.error(f"pdfplumber extraction failed: {e}")
            return ""
    
    def _extract_with_ocr(self, file_content: bytes) -> str:
        """Extract text using OCR for scanned PDFs."""
        try:
            from .ocr_parser import OCRParser
            
            ocr = OCRParser()
            return ocr.extract_from_pdf(file_content)
        except Exception as e:
            self.logger.warning(f"OCR extraction failed: {e}")
            return ""
    
    def _detect_bank(self, text: str) -> Optional[str]:
        """Detect which bank's format this is."""
        text_upper = text.upper()
        
        for bank_id, patterns in BANK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_upper, re.IGNORECASE):
                    return bank_id
        
        return None
    
    def _extract_account_info(self, text: str, result: ParserResult) -> None:
        """Extract account information from statement."""
        # Extract account number
        account_patterns = [
            r'A/C\s*(?:NO\.?)?\s*[:\s]*(\d{9,18})',
            r'ACCOUNT\s*(?:NO\.?|NUMBER)?\s*[:\s]*(\d{9,18})',
            r'ACCT\s*(?:NO\.?)?\s*[:\s]*(\d{9,18})',
        ]
        
        for pattern in account_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.account_number_masked = self.cleaner.mask_account_number(match.group(1))
                break
        
        # Extract statement period
        period_patterns = [
            r'STATEMENT\s*(?:FOR|OF)?\s*(?:THE)?\s*(?:PERIOD)?\s*[:\s]*(\d{1,2}[-/]\w{3}[-/]\d{2,4})\s*(?:TO|-)?\s*(\d{1,2}[-/]\w{3}[-/]\d{2,4})',
            r'FROM\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*TO\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'PERIOD\s*[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*[-–]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        ]
        
        for pattern in period_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start_date = self.cleaner.clean_date(match.group(1))
                end_date = self.cleaner.clean_date(match.group(2))
                if start_date and end_date:
                    result.statement_period = f"{start_date} to {end_date}"
                break
        
        # Extract account holder name
        name_patterns = [
            r'NAME\s*[:\s]*([A-Z][A-Z\s\.]+)',
            r'CUSTOMER\s*NAME\s*[:\s]*([A-Z][A-Z\s\.]+)',
            r'A/C\s*HOLDER\s*[:\s]*([A-Z][A-Z\s\.]+)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.account_holder = match.group(1).strip()
                break
        
        # Extract opening/closing balance
        balance_patterns = [
            (r'OPENING\s*BALANCE\s*[:\s]*([\d,]+\.?\d*)', 'opening'),
            (r'CLOSING\s*BALANCE\s*[:\s]*([\d,]+\.?\d*)', 'closing'),
            (r'BALANCE\s*B/F\s*[:\s]*([\d,]+\.?\d*)', 'opening'),
            (r'BALANCE\s*C/F\s*[:\s]*([\d,]+\.?\d*)', 'closing'),
        ]
        
        for pattern, balance_type in balance_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = self.cleaner.clean_amount(match.group(1))
                if amount is not None:
                    if balance_type == 'opening':
                        result.opening_balance = amount
                    else:
                        result.closing_balance = amount
    
    def _parse_hdfc_format(self, text: str) -> List[ParsedTransaction]:
        """
        Parse HDFC Bank statement format.
        
        Format example:
        Date        Narration                          Chq./Ref.No.    Value Dt    Withdrawal Amt.    Deposit Amt.    Closing Balance
        01/01/24    UPI/123456/SWIGGY                  123456789012    01/01/24    500.00                             45,000.00
        02/01/24    SALARY JAN-24                      NEFT12345       02/01/24                       50,000.00       95,000.00
        """
        transactions = []
        
        # HDFC pattern - handles multiline descriptions
        patterns = [
            # Standard format with all columns
            r'(\d{2}[/-]\d{2}[/-]\d{2,4})\s+(.+?)\s+(\d+)\s+\d{2}[/-]\d{2}[/-]\d{2,4}\s+([\d,]+\.?\d*)?\s*([\d,]+\.?\d*)?\s+([\d,]+\.?\d*)',
            # Simplified format
            r'(\d{2}[/-]\d{2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.?\d*)\s+(?:DR|CR)?\s*([\d,]+\.?\d*)?',
        ]
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    
                    date_str = groups[0]
                    description = groups[1].strip() if groups[1] else ""
                    
                    # Determine withdrawal/deposit
                    withdrawal = None
                    deposit = None
                    balance = None
                    
                    if len(groups) >= 6:
                        withdrawal = self.cleaner.clean_amount(groups[3]) if groups[3] else None
                        deposit = self.cleaner.clean_amount(groups[4]) if groups[4] else None
                        balance = self.cleaner.clean_amount(groups[5]) if groups[5] else None
                    elif len(groups) >= 4:
                        amount = self.cleaner.clean_amount(groups[2])
                        if 'DR' in line.upper():
                            withdrawal = amount
                        else:
                            deposit = amount
                        balance = self.cleaner.clean_amount(groups[3]) if groups[3] else None
                    
                    # Determine transaction type
                    if withdrawal and withdrawal > 0:
                        txn_type = TransactionType.DEBIT
                        amount = withdrawal
                    elif deposit and deposit > 0:
                        txn_type = TransactionType.CREDIT
                        amount = deposit
                    else:
                        continue
                    
                    # Clean date
                    clean_date = self.cleaner.clean_date(date_str)
                    if not clean_date:
                        continue
                    
                    txn = self._create_transaction(
                        date=clean_date,
                        description=description,
                        amount=amount,
                        transaction_type=txn_type,
                        balance=balance,
                        reference=self.cleaner.extract_reference(line),
                        raw_text=line,
                    )
                    
                    if txn:
                        transactions.append(txn)
                    break
        
        return transactions
    
    def _parse_sbi_format(self, text: str) -> List[ParsedTransaction]:
        """
        Parse SBI (State Bank of India) statement format.
        
        Format example:
        Txn Date    Value Date    Description                           Ref No./Cheque No.    Debit    Credit    Balance
        01 Jan 2024 01 Jan 2024   UPI/123456789/MERCHANT@bank           123456789             500.00            45000.00
        """
        transactions = []
        
        patterns = [
            # Standard SBI format
            r'(\d{1,2}\s+\w{3}\s+\d{4})\s+\d{1,2}\s+\w{3}\s+\d{4}\s+(.+?)\s+(\d+)?\s+([\d,]+\.?\d*)?\s+([\d,]+\.?\d*)?\s+([\d,]+\.?\d*)',
            # Alternate format
            r'(\d{2}[/-]\d{2}[/-]\d{4})\s+(.+?)\s+([\d,]+\.?\d*)\s+(DR|CR)\s+([\d,]+\.?\d*)',
        ]
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    date_str = groups[0]
                    description = groups[1].strip()
                    
                    if len(groups) >= 6:
                        debit = self.cleaner.clean_amount(groups[3]) if groups[3] else None
                        credit = self.cleaner.clean_amount(groups[4]) if groups[4] else None
                        balance = self.cleaner.clean_amount(groups[5]) if groups[5] else None
                    else:
                        amount = self.cleaner.clean_amount(groups[2])
                        if groups[3] and groups[3].upper() == 'DR':
                            debit = amount
                            credit = None
                        else:
                            credit = amount
                            debit = None
                        balance = self.cleaner.clean_amount(groups[4]) if len(groups) > 4 and groups[4] else None
                    
                    if debit and debit > 0:
                        txn_type = TransactionType.DEBIT
                        amount = debit
                    elif credit and credit > 0:
                        txn_type = TransactionType.CREDIT
                        amount = credit
                    else:
                        continue
                    
                    clean_date = self.cleaner.clean_date(date_str)
                    if not clean_date:
                        continue
                    
                    txn = self._create_transaction(
                        date=clean_date,
                        description=description,
                        amount=amount,
                        transaction_type=txn_type,
                        balance=balance,
                        reference=self.cleaner.extract_reference(line),
                        raw_text=line,
                    )
                    
                    if txn:
                        transactions.append(txn)
                    break
        
        return transactions
    
    def _parse_icici_format(self, text: str) -> List[ParsedTransaction]:
        """
        Parse ICICI Bank statement format.
        
        Format example:
        S No.    Value Date    Transaction Date    Cheque Number    Transaction Remarks    Withdrawal Amount (INR )    Deposit Amount (INR )    Balance (INR )
        1        01/01/2024    01/01/2024          --               UPI/123456/MERCHANT    500.00                                               45,000.00
        """
        transactions = []
        
        pattern = r'(\d+)\s+(\d{2}/\d{2}/\d{4})\s+\d{2}/\d{2}/\d{4}\s+[\w-]+\s+(.+?)\s+([\d,]+\.?\d*)?\s+([\d,]+\.?\d*)?\s+([\d,]+\.?\d*)'
        
        for line in text.split('\n'):
            line = line.strip()
            if not line or line.startswith('S No'):
                continue
            
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                
                date_str = groups[1]
                description = groups[2].strip()
                withdrawal = self.cleaner.clean_amount(groups[3]) if groups[3] else None
                deposit = self.cleaner.clean_amount(groups[4]) if groups[4] else None
                balance = self.cleaner.clean_amount(groups[5]) if groups[5] else None
                
                if withdrawal and withdrawal > 0:
                    txn_type = TransactionType.DEBIT
                    amount = withdrawal
                elif deposit and deposit > 0:
                    txn_type = TransactionType.CREDIT
                    amount = deposit
                else:
                    continue
                
                clean_date = self.cleaner.clean_date(date_str)
                if not clean_date:
                    continue
                
                txn = self._create_transaction(
                    date=clean_date,
                    description=description,
                    amount=amount,
                    transaction_type=txn_type,
                    balance=balance,
                    reference=self.cleaner.extract_reference(description),
                    raw_text=line,
                )
                
                if txn:
                    transactions.append(txn)
        
        return transactions
    
    def _parse_axis_format(self, text: str) -> List[ParsedTransaction]:
        """Parse Axis Bank statement format."""
        transactions = []
        
        # Axis format: Tran Date | Chq No | Particulars | Debit | Credit | Balance
        pattern = r'(\d{2}-\w{3}-\d{4})\s+(\d*)\s+(.+?)\s+([\d,]+\.?\d*)?\s+([\d,]+\.?\d*)?\s+([\d,]+\.?\d*)'
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                
                date_str = groups[0]
                description = groups[2].strip()
                debit = self.cleaner.clean_amount(groups[3]) if groups[3] else None
                credit = self.cleaner.clean_amount(groups[4]) if groups[4] else None
                balance = self.cleaner.clean_amount(groups[5]) if groups[5] else None
                
                if debit and debit > 0:
                    txn_type = TransactionType.DEBIT
                    amount = debit
                elif credit and credit > 0:
                    txn_type = TransactionType.CREDIT
                    amount = credit
                else:
                    continue
                
                clean_date = self.cleaner.clean_date(date_str)
                if not clean_date:
                    continue
                
                txn = self._create_transaction(
                    date=clean_date,
                    description=description,
                    amount=amount,
                    transaction_type=txn_type,
                    balance=balance,
                    reference=self.cleaner.extract_reference(line),
                    raw_text=line,
                )
                
                if txn:
                    transactions.append(txn)
        
        return transactions
    
    def _parse_kotak_format(self, text: str) -> List[ParsedTransaction]:
        """Parse Kotak Mahindra Bank statement format."""
        transactions = []
        
        pattern = r'(\d{2}[/-]\d{2}[/-]\d{4})\s+(.+?)\s+([\d,]+\.?\d*)\s+(DR|CR)\s+([\d,]+\.?\d*)'
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                date_str = groups[0]
                description = groups[1].strip()
                amount = self.cleaner.clean_amount(groups[2])
                dr_cr = groups[3].upper()
                balance = self.cleaner.clean_amount(groups[4])
                
                if not amount:
                    continue
                
                txn_type = TransactionType.DEBIT if dr_cr == 'DR' else TransactionType.CREDIT
                
                clean_date = self.cleaner.clean_date(date_str)
                if not clean_date:
                    continue
                
                txn = self._create_transaction(
                    date=clean_date,
                    description=description,
                    amount=amount,
                    transaction_type=txn_type,
                    balance=balance,
                    reference=self.cleaner.extract_reference(description),
                    raw_text=line,
                )
                
                if txn:
                    transactions.append(txn)
        
        return transactions
    
    def _parse_idfc_format(self, text: str) -> List[ParsedTransaction]:
        """Parse IDFC First Bank statement format."""
        return self._parse_generic_format(text)
    
    def _parse_yes_format(self, text: str) -> List[ParsedTransaction]:
        """Parse Yes Bank statement format."""
        return self._parse_generic_format(text)
    
    def _parse_scb_format(self, text: str) -> List[ParsedTransaction]:
        """Parse Standard Chartered Bank statement format."""
        return self._parse_generic_format(text)
    
    def _parse_citi_format(self, text: str) -> List[ParsedTransaction]:
        """Parse Citibank statement format."""
        return self._parse_generic_format(text)
    
    def _parse_pnb_format(self, text: str) -> List[ParsedTransaction]:
        """Parse PNB statement format."""
        return self._parse_sbi_format(text)  # Similar format to SBI
    
    def _parse_bob_format(self, text: str) -> List[ParsedTransaction]:
        """Parse Bank of Baroda statement format."""
        return self._parse_sbi_format(text)
    
    def _parse_canara_format(self, text: str) -> List[ParsedTransaction]:
        """Parse Canara Bank statement format."""
        return self._parse_sbi_format(text)
    
    def _parse_indusind_format(self, text: str) -> List[ParsedTransaction]:
        """Parse IndusInd Bank statement format."""
        return self._parse_axis_format(text)
    
    def _parse_federal_format(self, text: str) -> List[ParsedTransaction]:
        """Parse Federal Bank statement format."""
        return self._parse_generic_format(text)
    
    def _parse_rbl_format(self, text: str) -> List[ParsedTransaction]:
        """Parse RBL Bank statement format."""
        return self._parse_generic_format(text)
    
    def _parse_generic_format(self, text: str) -> List[ParsedTransaction]:
        """
        Generic parser for unknown bank formats.
        
        Attempts to find common transaction patterns.
        """
        transactions = []
        
        # Generic patterns to try
        patterns = [
            # Pattern 1: Date Description Amount DR/CR Balance
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.?\d+)\s*(DR|CR|D|C)?\s*([\d,]+\.?\d+)?',
            # Pattern 2: Date Description Debit Credit Balance
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.?\d*)?\s+([\d,]+\.?\d*)?\s+([\d,]+\.?\d+)',
            # Pattern 3: DD Mon YYYY format
            r'(\d{1,2}\s+\w{3}\s+\d{4})\s+(.+?)\s+([\d,]+\.?\d+)\s*(DR|CR)?\s*([\d,]+\.?\d+)?',
        ]
        
        for line in text.split('\n'):
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Skip header lines
            if any(header in line.upper() for header in ['DATE', 'DESCRIPTION', 'BALANCE', 'NARRATION', 'PARTICULARS']):
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    date_str = groups[0]
                    description = groups[1].strip() if groups[1] else ""
                    
                    # Skip if description is too short or looks like headers
                    if len(description) < 3:
                        continue
                    
                    # Determine amount and type
                    amount = None
                    txn_type = TransactionType.UNKNOWN
                    balance = None
                    
                    if len(groups) >= 5:
                        # Check for DR/CR indicator
                        if groups[3] and groups[3].upper() in ['DR', 'D']:
                            amount = self.cleaner.clean_amount(groups[2])
                            txn_type = TransactionType.DEBIT
                        elif groups[3] and groups[3].upper() in ['CR', 'C']:
                            amount = self.cleaner.clean_amount(groups[2])
                            txn_type = TransactionType.CREDIT
                        else:
                            # Assume debit/credit columns
                            debit = self.cleaner.clean_amount(groups[2]) if groups[2] else None
                            credit = self.cleaner.clean_amount(groups[3]) if groups[3] else None
                            
                            if debit and debit > 0:
                                amount = debit
                                txn_type = TransactionType.DEBIT
                            elif credit and credit > 0:
                                amount = credit
                                txn_type = TransactionType.CREDIT
                        
                        balance = self.cleaner.clean_amount(groups[4]) if groups[4] else None
                    elif len(groups) >= 3:
                        amount = self.cleaner.clean_amount(groups[2])
                        txn_type = self.cleaner.detect_transaction_type(description)
                    
                    if not amount or amount <= 0:
                        continue
                    
                    clean_date = self.cleaner.clean_date(date_str)
                    if not clean_date:
                        continue
                    
                    txn = self._create_transaction(
                        date=clean_date,
                        description=description,
                        amount=amount,
                        transaction_type=txn_type,
                        balance=balance,
                        reference=self.cleaner.extract_reference(line),
                        raw_text=line,
                        confidence=0.7,  # Lower confidence for generic parser
                    )
                    
                    if txn:
                        transactions.append(txn)
                    break
        
        return transactions
