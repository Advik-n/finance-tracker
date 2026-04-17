"""
CSV Statement Parser for Bank and Payment App Exports

Parses CSV exports from bank portals and payment apps with automatic
format detection and column mapping.
"""

import io
import re
import logging
import chardet
from typing import List, Optional, Dict, Any, Tuple
import time

from .base_parser import (
    BaseParser,
    ParsedTransaction,
    ParserResult,
    TransactionType,
    ParserError,
)
from .cleaners import DataCleaner, TransactionCategorizer

logger = logging.getLogger(__name__)


class CSVStatementParser(BaseParser):
    """
    Parse CSV exports from various sources.
    
    Supports:
    - Bank portal exports (HDFC, SBI, ICICI, Axis, etc.)
    - Google Pay export
    - PhonePe export
    - Paytm export
    - Amazon Pay export
    - Custom CSV with configurable columns
    """
    
    PARSER_NAME = "CSVStatementParser"
    PARSER_VERSION = "1.0.0"
    SUPPORTED_FORMATS = [".csv", ".txt"]
    
    # Column mappings for different sources
    COLUMN_MAPPINGS = {
        "gpay": {
            "date": ["Date", "Transaction Date", "date"],
            "description": ["Description", "Merchant", "To/From", "description"],
            "amount": ["Amount", "Transaction Amount", "amount"],
            "type": ["Transaction Type", "Type", "Status", "type"],
            "reference": ["Transaction ID", "Reference", "UPI ID", "reference"],
        },
        "phonepe": {
            "date": ["Date", "Transaction Date", "date"],
            "description": ["Payee Name", "Description", "Merchant", "description"],
            "amount": ["Amount", "Transaction Amount", "amount"],
            "type": ["Transaction Type", "Type", "type"],
            "reference": ["Transaction ID", "UTR", "reference"],
        },
        "paytm": {
            "date": ["Date", "Transaction Date", "Order Date", "date"],
            "description": ["Description", "Merchant Name", "Order Details", "description"],
            "amount": ["Amount", "Transaction Amount", "Total Amount", "amount"],
            "type": ["Transaction Type", "Type", "Status", "type"],
            "reference": ["Order ID", "Transaction ID", "reference"],
        },
        "amazonpay": {
            "date": ["Date", "Transaction Date", "date"],
            "description": ["Description", "Merchant", "Order Description", "description"],
            "amount": ["Amount", "Transaction Amount", "amount"],
            "type": ["Transaction Type", "Type", "type"],
            "reference": ["Order ID", "Transaction ID", "reference"],
        },
        "hdfc": {
            "date": ["Date", "Txn Date", "Transaction Date", "Value Date"],
            "description": ["Narration", "Description", "Particulars", "Transaction Description"],
            "withdrawal": ["Withdrawal Amt.", "Withdrawal Amount", "Debit", "Debit Amount"],
            "deposit": ["Deposit Amt.", "Deposit Amount", "Credit", "Credit Amount"],
            "balance": ["Closing Balance", "Balance", "Running Balance"],
            "reference": ["Chq./Ref.No.", "Reference No.", "Cheque No"],
        },
        "sbi": {
            "date": ["Txn Date", "Transaction Date", "Value Date", "Date"],
            "description": ["Description", "Narration", "Particulars"],
            "withdrawal": ["Debit", "Withdrawal", "Debit Amount"],
            "deposit": ["Credit", "Deposit", "Credit Amount"],
            "balance": ["Balance", "Closing Balance"],
            "reference": ["Ref No./Cheque No.", "Reference", "Txn Reference"],
        },
        "icici": {
            "date": ["Value Date", "Transaction Date", "Date"],
            "description": ["Transaction Remarks", "Remarks", "Description"],
            "withdrawal": ["Withdrawal Amount (INR )", "Withdrawal", "Debit"],
            "deposit": ["Deposit Amount (INR )", "Deposit", "Credit"],
            "balance": ["Balance (INR )", "Balance"],
            "reference": ["Cheque Number", "Reference"],
        },
        "axis": {
            "date": ["Tran Date", "Transaction Date", "Date"],
            "description": ["Particulars", "Description", "Narration"],
            "withdrawal": ["Debit", "Withdrawal", "Dr Amount"],
            "deposit": ["Credit", "Deposit", "Cr Amount"],
            "balance": ["Balance", "Closing Balance"],
            "reference": ["Chq No", "Reference"],
        },
        "kotak": {
            "date": ["Date", "Transaction Date", "Value Date"],
            "description": ["Description", "Narration", "Particulars"],
            "amount": ["Amount", "Transaction Amount"],
            "type_indicator": ["Dr / Cr", "Type", "DR/CR"],
            "balance": ["Balance", "Closing Balance"],
        },
        "generic": {
            "date": ["Date", "Txn Date", "Transaction Date", "Value Date", "date"],
            "description": ["Description", "Narration", "Particulars", "Details", "Remarks", "description"],
            "amount": ["Amount", "Transaction Amount", "Txn Amount", "amount"],
            "withdrawal": ["Withdrawal", "Debit", "Dr", "Withdrawal Amount", "withdrawal"],
            "deposit": ["Deposit", "Credit", "Cr", "Deposit Amount", "deposit"],
            "balance": ["Balance", "Closing Balance", "Running Balance", "balance"],
            "type": ["Type", "Transaction Type", "Dr/Cr", "type"],
            "reference": ["Reference", "Ref No", "Transaction ID", "Cheque No", "reference"],
        },
    }
    
    # Delimiters to try
    DELIMITERS = [',', ';', '\t', '|']
    
    # Encodings to try
    ENCODINGS = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 
                 'windows-1252', 'iso-8859-1', 'cp1252', 'latin-1']
    
    def __init__(self):
        """Initialize the CSV parser."""
        super().__init__()
        self.cleaner = DataCleaner()
        self.categorizer = TransactionCategorizer()
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """Check if this parser can handle the file."""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return ext in ['csv', 'txt']
    
    def parse(self, file_content: bytes, filename: str) -> ParserResult:
        """
        Parse a CSV statement file.
        
        Args:
            file_content: Raw CSV bytes
            filename: Original filename
            
        Returns:
            ParserResult with parsed transactions
        """
        start_time = time.time()
        result = self._create_result(filename)
        
        try:
            # Detect encoding
            encoding = self._detect_encoding(file_content)
            self.logger.info(f"Detected encoding: {encoding}")
            
            # Decode content
            try:
                text_content = file_content.decode(encoding)
            except UnicodeDecodeError:
                # Fallback to latin-1 which accepts all byte values
                text_content = file_content.decode('latin-1')
                result.add_warning(f"Encoding detection failed, using fallback")
            
            # Import pandas here to avoid startup overhead
            import pandas as pd
            
            # Detect delimiter
            delimiter = self._detect_delimiter(text_content)
            self.logger.info(f"Detected delimiter: '{delimiter}'")
            
            # Find header row (skip metadata rows at top)
            header_row, skip_rows = self._find_header_row(text_content, delimiter)
            
            # Read CSV
            try:
                df = pd.read_csv(
                    io.StringIO(text_content),
                    delimiter=delimiter,
                    skiprows=skip_rows,
                    skip_blank_lines=True,
                    on_bad_lines='skip',
                    engine='python',
                )
            except Exception as e:
                self.logger.warning(f"Pandas read failed: {e}, trying without skip")
                df = pd.read_csv(
                    io.StringIO(text_content),
                    delimiter=delimiter,
                    on_bad_lines='skip',
                    engine='python',
                )
            
            if df.empty:
                result.add_error("CSV file is empty or could not be parsed")
                return result
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Detect format
            format_type = self._detect_csv_format(df)
            result.metadata['detected_format'] = format_type
            self.logger.info(f"Detected CSV format: {format_type}")
            
            # Map columns to standard format
            column_map = self._map_columns(df, format_type)
            
            if not column_map:
                result.add_error("Could not map CSV columns to transaction fields")
                return result
            
            # Parse transactions
            transactions = self._parse_dataframe(df, column_map, result)
            
            # Clean and add transactions
            for txn in transactions:
                if txn:
                    if not txn.category:
                        txn.category = self.categorizer.categorize(txn.description)
                    result.transactions.append(txn)
            
            # Detect bank name from content
            result.bank_name = self._detect_bank_from_content(text_content, df)
            
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
            self.logger.error(f"CSV parsing error: {e}", exc_info=True)
            result.add_error(f"CSV parsing failed: {str(e)}")
            result.parsing_time_ms = (time.time() - start_time) * 1000
            return result
    
    def _detect_encoding(self, content: bytes) -> str:
        """Detect the encoding of the file content."""
        # Check for BOM
        if content.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'
        if content.startswith(b'\xff\xfe'):
            return 'utf-16-le'
        if content.startswith(b'\xfe\xff'):
            return 'utf-16-be'
        
        # Use chardet for detection
        try:
            detected = chardet.detect(content)
            if detected and detected.get('encoding'):
                confidence = detected.get('confidence', 0)
                if confidence > 0.7:
                    return detected['encoding']
        except Exception:
            pass
        
        # Try each encoding
        for encoding in self.ENCODINGS:
            try:
                content.decode(encoding)
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        return 'utf-8'
    
    def _detect_delimiter(self, text: str) -> str:
        """Detect the CSV delimiter."""
        # Take first few lines for analysis
        lines = text.split('\n')[:10]
        sample = '\n'.join(lines)
        
        delimiter_counts = {}
        for delim in self.DELIMITERS:
            # Count occurrences per line
            counts = [line.count(delim) for line in lines if line.strip()]
            if counts:
                # Check if count is consistent across lines
                avg_count = sum(counts) / len(counts)
                variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
                
                # Prefer delimiters with consistent counts and multiple occurrences
                if avg_count > 0 and variance < 2:
                    delimiter_counts[delim] = avg_count
        
        if delimiter_counts:
            # Return delimiter with highest consistent count
            return max(delimiter_counts, key=delimiter_counts.get)
        
        return ','  # Default to comma
    
    def _find_header_row(self, text: str, delimiter: str) -> Tuple[int, int]:
        """Find the header row, skipping metadata rows."""
        lines = text.split('\n')
        
        # Keywords that indicate a header row
        header_keywords = [
            'date', 'description', 'amount', 'balance', 'narration',
            'particulars', 'debit', 'credit', 'withdrawal', 'deposit',
            'transaction', 'reference', 'type', 'status'
        ]
        
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            line_lower = line.lower()
            
            # Count header keywords in this line
            keyword_count = sum(1 for kw in header_keywords if kw in line_lower)
            
            # Also check if it has multiple columns
            col_count = len(line.split(delimiter))
            
            if keyword_count >= 2 and col_count >= 3:
                return i, i
        
        return 0, 0  # No header found, use first row
    
    def _detect_csv_format(self, df) -> str:
        """Detect which CSV format this is."""
        columns = [col.lower() for col in df.columns]
        columns_str = ' '.join(columns)
        
        # Check for specific format indicators
        if 'narration' in columns_str and ('withdrawal' in columns_str or 'deposit' in columns_str):
            if 'hdfc' in columns_str:
                return 'hdfc'
            return 'hdfc'  # HDFC-like format
        
        if 'transaction remarks' in columns_str:
            return 'icici'
        
        if 'particulars' in columns_str and 'tran date' in columns_str:
            return 'axis'
        
        if 'dr / cr' in columns_str or 'dr/cr' in columns_str:
            return 'kotak'
        
        # Check for payment app formats
        if 'merchant' in columns_str or 'payee' in columns_str:
            if 'upi' in columns_str:
                return 'gpay'
            return 'phonepe'
        
        if 'order' in columns_str:
            if 'amazon' in columns_str:
                return 'amazonpay'
            return 'paytm'
        
        # Check for SBI-like format
        if 'txn date' in columns_str and 'ref no' in columns_str:
            return 'sbi'
        
        return 'generic'
    
    def _map_columns(self, df, format_type: str) -> Dict[str, str]:
        """Map DataFrame columns to standard field names."""
        mapping = self.COLUMN_MAPPINGS.get(format_type, self.COLUMN_MAPPINGS['generic'])
        column_map = {}
        
        df_columns = {col.lower(): col for col in df.columns}
        
        for field, possible_names in mapping.items():
            for name in possible_names:
                name_lower = name.lower()
                if name_lower in df_columns:
                    column_map[field] = df_columns[name_lower]
                    break
        
        # Verify we have minimum required fields
        has_date = 'date' in column_map
        has_description = 'description' in column_map
        has_amount = 'amount' in column_map or ('withdrawal' in column_map or 'deposit' in column_map)
        
        if has_date and has_description and has_amount:
            return column_map
        
        # Try fuzzy matching
        return self._fuzzy_map_columns(df)
    
    def _fuzzy_map_columns(self, df) -> Dict[str, str]:
        """Fuzzy match column names when exact match fails."""
        column_map = {}
        df_columns = list(df.columns)
        
        # Date patterns
        for col in df_columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['date', 'dt', 'time']):
                column_map['date'] = col
                break
        
        # Description patterns
        for col in df_columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['desc', 'narr', 'particular', 'detail', 'remark']):
                column_map['description'] = col
                break
        
        # Amount patterns
        for col in df_columns:
            col_lower = col.lower()
            if 'amount' in col_lower or 'amt' in col_lower:
                if 'withdraw' in col_lower or 'debit' in col_lower or 'dr' in col_lower:
                    column_map['withdrawal'] = col
                elif 'deposit' in col_lower or 'credit' in col_lower or 'cr' in col_lower:
                    column_map['deposit'] = col
                else:
                    column_map['amount'] = col
        
        # Balance pattern
        for col in df_columns:
            if 'balance' in col.lower() or 'bal' in col.lower():
                column_map['balance'] = col
                break
        
        return column_map
    
    def _parse_dataframe(
        self,
        df,
        column_map: Dict[str, str],
        result: ParserResult
    ) -> List[ParsedTransaction]:
        """Parse transactions from DataFrame."""
        transactions = []
        
        for idx, row in df.iterrows():
            try:
                txn = self._parse_row(row, column_map, idx)
                if txn:
                    transactions.append(txn)
            except Exception as e:
                result.add_warning(f"Failed to parse row {idx}: {str(e)}")
        
        return transactions
    
    def _parse_row(
        self,
        row,
        column_map: Dict[str, str],
        idx: int
    ) -> Optional[ParsedTransaction]:
        """Parse a single row into a transaction."""
        import pandas as pd
        
        # Extract date
        date_col = column_map.get('date')
        if not date_col or pd.isna(row.get(date_col)):
            return None
        
        date_val = str(row[date_col]).strip()
        clean_date = self.cleaner.clean_date(date_val)
        if not clean_date:
            return None
        
        # Extract description
        desc_col = column_map.get('description')
        description = ""
        if desc_col and not pd.isna(row.get(desc_col)):
            description = self.cleaner.clean_description(str(row[desc_col]))
        
        # Extract amount and type
        amount = None
        txn_type = TransactionType.UNKNOWN
        
        # Check for separate withdrawal/deposit columns
        withdrawal_col = column_map.get('withdrawal')
        deposit_col = column_map.get('deposit')
        
        if withdrawal_col or deposit_col:
            withdrawal = None
            deposit = None
            
            if withdrawal_col and not pd.isna(row.get(withdrawal_col)):
                withdrawal = self.cleaner.clean_amount(str(row[withdrawal_col]))
            
            if deposit_col and not pd.isna(row.get(deposit_col)):
                deposit = self.cleaner.clean_amount(str(row[deposit_col]))
            
            if withdrawal and withdrawal > 0:
                amount = withdrawal
                txn_type = TransactionType.DEBIT
            elif deposit and deposit > 0:
                amount = deposit
                txn_type = TransactionType.CREDIT
        
        # Check for single amount column
        if amount is None:
            amount_col = column_map.get('amount')
            if amount_col and not pd.isna(row.get(amount_col)):
                amount = self.cleaner.clean_amount(str(row[amount_col]))
                
                # Check for type indicator
                type_col = column_map.get('type') or column_map.get('type_indicator')
                if type_col and not pd.isna(row.get(type_col)):
                    type_val = str(row[type_col]).upper().strip()
                    if type_val in ['DR', 'D', 'DEBIT', 'WITHDRAWAL', '-']:
                        txn_type = TransactionType.DEBIT
                    elif type_val in ['CR', 'C', 'CREDIT', 'DEPOSIT', '+']:
                        txn_type = TransactionType.CREDIT
                
                # If still unknown, try to detect from description or amount sign
                if txn_type == TransactionType.UNKNOWN:
                    txn_type = self.cleaner.detect_transaction_type(
                        description,
                        amount=amount
                    )
        
        if amount is None or amount == 0:
            return None
        
        # Extract balance
        balance = None
        balance_col = column_map.get('balance')
        if balance_col and not pd.isna(row.get(balance_col)):
            balance = self.cleaner.clean_amount(str(row[balance_col]))
        
        # Extract reference
        reference = None
        ref_col = column_map.get('reference')
        if ref_col and not pd.isna(row.get(ref_col)):
            reference = str(row[ref_col]).strip()
        
        if not reference:
            reference = self.cleaner.extract_reference(description)
        
        # Build raw text from row
        raw_text = ' | '.join(str(v) for v in row.values if not pd.isna(v))
        
        return self._create_transaction(
            date=clean_date,
            description=description,
            amount=abs(amount),
            transaction_type=txn_type,
            balance=balance,
            reference=reference,
            raw_text=raw_text[:500],  # Limit raw text length
        )
    
    def _detect_bank_from_content(self, text: str, df) -> Optional[str]:
        """Try to detect bank name from CSV content."""
        text_upper = text.upper()
        
        bank_indicators = {
            'HDFC': ['HDFC BANK', 'HDFCBANK'],
            'SBI': ['STATE BANK OF INDIA', 'SBI'],
            'ICICI': ['ICICI BANK', 'ICICIBANK'],
            'AXIS': ['AXIS BANK', 'AXISBANK'],
            'KOTAK': ['KOTAK MAHINDRA', 'KOTAK BANK'],
            'IDFC FIRST': ['IDFC FIRST', 'IDFC BANK'],
            'YES': ['YES BANK', 'YESBANK'],
            'GOOGLE PAY': ['GOOGLE PAY', 'GPAY'],
            'PHONEPE': ['PHONEPE'],
            'PAYTM': ['PAYTM'],
            'AMAZON PAY': ['AMAZON PAY'],
        }
        
        for bank_name, indicators in bank_indicators.items():
            for indicator in indicators:
                if indicator in text_upper:
                    return bank_name
        
        return None
    
    def parse_with_config(
        self,
        file_content: bytes,
        filename: str,
        column_config: Dict[str, str]
    ) -> ParserResult:
        """
        Parse CSV with user-provided column mapping.
        
        Args:
            file_content: Raw CSV bytes
            filename: Original filename
            column_config: User-specified column mapping
                          {
                              "date": "My Date Column",
                              "description": "My Description",
                              "amount": "Amount",
                              ...
                          }
        
        Returns:
            ParserResult with parsed transactions
        """
        start_time = time.time()
        result = self._create_result(filename)
        
        try:
            import pandas as pd
            
            # Detect encoding and delimiter
            encoding = self._detect_encoding(file_content)
            text_content = file_content.decode(encoding)
            delimiter = self._detect_delimiter(text_content)
            
            # Read CSV
            df = pd.read_csv(
                io.StringIO(text_content),
                delimiter=delimiter,
                on_bad_lines='skip',
            )
            
            # Validate user-provided column mapping
            valid_config = {}
            for field, col_name in column_config.items():
                if col_name in df.columns:
                    valid_config[field] = col_name
                else:
                    result.add_warning(f"Column '{col_name}' not found for field '{field}'")
            
            if 'date' not in valid_config:
                result.add_error("Date column mapping is required")
                return result
            
            # Parse transactions
            transactions = self._parse_dataframe(df, valid_config, result)
            
            for txn in transactions:
                if txn:
                    if not txn.category:
                        txn.category = self.categorizer.categorize(txn.description)
                    result.transactions.append(txn)
            
            result.parsing_time_ms = (time.time() - start_time) * 1000
            return result
            
        except Exception as e:
            self.logger.error(f"CSV parsing with config error: {e}", exc_info=True)
            result.add_error(f"CSV parsing failed: {str(e)}")
            result.parsing_time_ms = (time.time() - start_time) * 1000
            return result


# Alias for backwards compatibility
CSVParser = CSVStatementParser
