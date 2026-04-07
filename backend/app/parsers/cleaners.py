"""
Data Cleaning Utilities for Bank Statement Parsing

Provides utilities for cleaning and normalizing parsed transaction data
including amounts, dates, descriptions, and duplicate detection.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
from difflib import SequenceMatcher

from .base_parser import ParsedTransaction, TransactionType

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Clean and normalize parsed transaction data.
    
    Handles various formats from different banks and payment providers.
    """
    
    # Amount patterns
    AMOUNT_PATTERNS = [
        # Indian Rupee symbol with amount: ₹1,234.56
        (r'[₹Rs\.?\s]*([0-9,]+\.?\d*)', lambda m: m.group(1)),
        # CR/DR suffix: 1234.56 CR
        (r'([0-9,]+\.?\d*)\s*(CR|DR|Cr|Dr)?', lambda m: m.group(1)),
        # Parentheses for negative: (1,234.56)
        (r'\(([0-9,]+\.?\d*)\)', lambda m: f"-{m.group(1)}"),
        # INR prefix: INR 1234.56
        (r'INR\s*([0-9,]+\.?\d*)', lambda m: m.group(1)),
        # Plain number with commas
        (r'([0-9,]+\.?\d*)', lambda m: m.group(1)),
    ]
    
    # Date format patterns (order matters - more specific first)
    DATE_FORMATS = [
        # ISO format
        ("%Y-%m-%d", r'^\d{4}-\d{2}-\d{2}$'),
        # DD/MM/YYYY
        ("%d/%m/%Y", r'^\d{2}/\d{2}/\d{4}$'),
        # DD-MM-YYYY
        ("%d-%m-%Y", r'^\d{2}-\d{2}-\d{4}$'),
        # YYYY/MM/DD
        ("%Y/%m/%d", r'^\d{4}/\d{2}/\d{2}$'),
        # MM/DD/YYYY (US format - less common in India)
        ("%m/%d/%Y", r'^\d{2}/\d{2}/\d{4}$'),
        # DD Mon YYYY (01 Jan 2024)
        ("%d %b %Y", r'^\d{2}\s+\w{3}\s+\d{4}$'),
        # DD-Mon-YYYY (01-Jan-2024)
        ("%d-%b-%Y", r'^\d{2}-\w{3}-\d{4}$'),
        # DD Mon YY (01 Jan 24)
        ("%d %b %y", r'^\d{2}\s+\w{3}\s+\d{2}$'),
        # DD-Mon-YY (01-Jan-24)
        ("%d-%b-%y", r'^\d{2}-\w{3}-\d{2}$'),
        # D/M/YYYY (single digit day/month)
        ("%d/%m/%Y", r'^\d{1,2}/\d{1,2}/\d{4}$'),
        # DD/MM/YY
        ("%d/%m/%y", r'^\d{2}/\d{2}/\d{2}$'),
        # DDMMYYYY (no separator)
        ("%d%m%Y", r'^\d{8}$'),
        # Mon DD, YYYY (Jan 01, 2024)
        ("%b %d, %Y", r'^\w{3}\s+\d{2},\s*\d{4}$'),
        # Month DD, YYYY (January 01, 2024)
        ("%B %d, %Y", r'^\w+\s+\d{2},\s*\d{4}$'),
    ]
    
    # UPI reference patterns
    UPI_PATTERNS = [
        r'UPI[-/]?(\d+)[-/]?([A-Za-z0-9@._]+)',
        r'UPI\s*REF[:\s]*(\d+)',
        r'UPI[-/]([A-Za-z0-9]+)',
        r'IMPS[-/](\d+)',
        r'NEFT[-/]([A-Za-z0-9]+)',
        r'RTGS[-/]([A-Za-z0-9]+)',
    ]
    
    # Common merchant patterns for normalization
    MERCHANT_PATTERNS = {
        r'SWIGGY\s*\d*': 'SWIGGY',
        r'ZOMATO\s*\d*': 'ZOMATO',
        r'AMAZON\s*(PAY)?\s*\d*': 'AMAZON',
        r'FLIPKART\s*\d*': 'FLIPKART',
        r'UBER\s*(INDIA)?\s*\d*': 'UBER',
        r'OLA\s*(CABS?)?\s*\d*': 'OLA',
        r'BIGBASKET\s*\d*': 'BIGBASKET',
        r'GROFERS\s*\d*': 'BLINKIT',
        r'BLINKIT\s*\d*': 'BLINKIT',
        r'ZERODHA\s*\d*': 'ZERODHA',
        r'GROWW\s*\d*': 'GROWW',
        r'PHONEPE\s*\d*': 'PHONEPE',
        r'GPAY\s*\d*': 'GOOGLE PAY',
        r'GOOGLE\s*PAY\s*\d*': 'GOOGLE PAY',
        r'PAYTM\s*\d*': 'PAYTM',
        r'NETFLIX\s*\d*': 'NETFLIX',
        r'SPOTIFY\s*\d*': 'SPOTIFY',
        r'YOUTUBE\s*\d*': 'YOUTUBE',
        r'HOTSTAR\s*\d*': 'HOTSTAR',
        r'PRIME\s*VIDEO\s*\d*': 'AMAZON PRIME',
    }
    
    def __init__(self):
        """Initialize the data cleaner"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def clean_amount(self, amount_str: str) -> Optional[float]:
        """
        Clean and parse amount string to float.
        
        Handles various formats:
        - ₹1,234.56
        - 1234.56 CR / 1234.56 DR
        - -1,234.56
        - (1,234.56) - negative in accounting format
        - INR 1234.56
        - Rs. 1,234.56
        - 1,23,456.78 - Indian numbering
        
        Args:
            amount_str: Raw amount string
            
        Returns:
            Parsed float amount or None if parsing fails
        """
        if not amount_str:
            return None
        
        try:
            # Remove whitespace
            amount_str = str(amount_str).strip()
            
            # Handle empty or null values
            if not amount_str or amount_str.lower() in ['null', 'none', '-', '--', 'n/a', '']:
                return None
            
            # Check for negative indicators
            is_negative = False
            if amount_str.startswith('(') and amount_str.endswith(')'):
                is_negative = True
                amount_str = amount_str[1:-1]
            elif amount_str.startswith('-'):
                is_negative = True
                amount_str = amount_str[1:]
            elif 'DR' in amount_str.upper() or 'DEBIT' in amount_str.upper():
                is_negative = True
            
            # Remove currency symbols and text
            amount_str = re.sub(r'[₹$€£¥]', '', amount_str)
            amount_str = re.sub(r'\b(Rs\.?|INR|CR|DR|CREDIT|DEBIT)\b', '', amount_str, flags=re.IGNORECASE)
            
            # Remove spaces
            amount_str = amount_str.replace(' ', '')
            
            # Handle Indian numbering system (1,23,456.78)
            # Remove all commas
            amount_str = amount_str.replace(',', '')
            
            # Remove any remaining non-numeric characters except decimal point and minus
            amount_str = re.sub(r'[^\d.\-]', '', amount_str)
            
            # Handle multiple decimal points (take first occurrence)
            parts = amount_str.split('.')
            if len(parts) > 2:
                amount_str = parts[0] + '.' + ''.join(parts[1:])
            
            if not amount_str:
                return None
                
            amount = float(amount_str)
            
            if is_negative:
                amount = -abs(amount)
            
            return amount
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to parse amount '{amount_str}': {e}")
            return None
    
    def clean_date(self, date_str: str, preferred_format: str = None) -> Optional[str]:
        """
        Parse various date formats and return ISO format (YYYY-MM-DD).
        
        Handles formats:
        - DD/MM/YYYY, DD-MM-YYYY
        - YYYY-MM-DD, YYYY/MM/DD
        - DD Mon YYYY, DD-Mon-YY
        - And more...
        
        Args:
            date_str: Raw date string
            preferred_format: Optional specific format to try first
            
        Returns:
            ISO format date string or None if parsing fails
        """
        if not date_str:
            return None
        
        try:
            date_str = str(date_str).strip()
            
            # Handle empty values
            if not date_str or date_str.lower() in ['null', 'none', '-', '', 'n/a']:
                return None
            
            # Remove extra whitespace
            date_str = ' '.join(date_str.split())
            
            # Try preferred format first
            if preferred_format:
                try:
                    dt = datetime.strptime(date_str, preferred_format)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass
            
            # Try each format
            for fmt, pattern in self.DATE_FORMATS:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    
                    # Handle 2-digit years
                    if dt.year < 100:
                        # Assume 20xx for years < 50, 19xx otherwise
                        if dt.year < 50:
                            dt = dt.replace(year=2000 + dt.year)
                        else:
                            dt = dt.replace(year=1900 + dt.year)
                    
                    # Validate reasonable date range (not in future, not too old)
                    now = datetime.now()
                    if dt > now + timedelta(days=1):
                        # Date is in future - might be wrong format
                        continue
                    if dt < datetime(1990, 1, 1):
                        # Too old - might be wrong format
                        continue
                    
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            # Try pandas for more flexible parsing
            try:
                import pandas as pd
                dt = pd.to_datetime(date_str, dayfirst=True)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
            
            self.logger.warning(f"Failed to parse date: '{date_str}'")
            return None
            
        except Exception as e:
            self.logger.warning(f"Date parsing error for '{date_str}': {e}")
            return None
    
    def clean_description(self, desc: str) -> str:
        """
        Clean and normalize transaction description.
        
        Operations:
        - Remove extra whitespace
        - Handle special characters
        - Normalize UPI format
        - Standardize common merchant names
        
        Args:
            desc: Raw description string
            
        Returns:
            Cleaned description string
        """
        if not desc:
            return ""
        
        try:
            desc = str(desc).strip()
            
            # Remove multiple spaces
            desc = ' '.join(desc.split())
            
            # Remove control characters
            desc = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', desc)
            
            # Normalize common Unicode characters
            replacements = {
                '\u2013': '-',  # en-dash
                '\u2014': '-',  # em-dash
                '\u2018': "'",  # left single quote
                '\u2019': "'",  # right single quote
                '\u201c': '"',  # left double quote
                '\u201d': '"',  # right double quote
                '\u00a0': ' ',  # non-breaking space
            }
            for old, new in replacements.items():
                desc = desc.replace(old, new)
            
            # Normalize merchant names
            desc_upper = desc.upper()
            for pattern, normalized in self.MERCHANT_PATTERNS.items():
                if re.search(pattern, desc_upper, re.IGNORECASE):
                    # Keep original case but ensure merchant name is present
                    break
            
            # Clean up UPI transaction format
            # UPI/123456789012/MERCHANT@BANK -> UPI MERCHANT
            upi_match = re.match(r'UPI[-/](\d+)[-/]([^@/]+)[@/]?', desc, re.IGNORECASE)
            if upi_match:
                merchant = upi_match.group(2).strip()
                desc = f"UPI - {merchant} ({desc})"
            
            return desc.strip()
            
        except Exception as e:
            self.logger.warning(f"Description cleaning error: {e}")
            return str(desc) if desc else ""
    
    def extract_reference(self, text: str) -> Optional[str]:
        """
        Extract transaction reference number from text.
        
        Args:
            text: Transaction description or raw text
            
        Returns:
            Reference number or None
        """
        if not text:
            return None
        
        for pattern in self.UPI_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Generic reference patterns
        ref_patterns = [
            r'REF\s*(?:NO\.?|NUMBER)?[:\s]*([A-Za-z0-9]+)',
            r'TXN\s*(?:ID|NO)?[:\s]*([A-Za-z0-9]+)',
            r'TRANS(?:ACTION)?\s*(?:ID|NO)?[:\s]*([A-Za-z0-9]+)',
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def detect_transaction_type(
        self,
        description: str,
        amount: float = None,
        withdrawal: float = None,
        deposit: float = None,
        credit_indicator: str = None
    ) -> TransactionType:
        """
        Detect transaction type (CREDIT/DEBIT) from available data.
        
        Args:
            description: Transaction description
            amount: Transaction amount (negative for debit)
            withdrawal: Withdrawal amount column
            deposit: Deposit amount column
            credit_indicator: CR/DR indicator
            
        Returns:
            TransactionType enum
        """
        # Check explicit indicator
        if credit_indicator:
            indicator = credit_indicator.upper().strip()
            if indicator in ['CR', 'C', 'CREDIT', '+']:
                return TransactionType.CREDIT
            elif indicator in ['DR', 'D', 'DEBIT', '-']:
                return TransactionType.DEBIT
        
        # Check separate columns
        if withdrawal is not None and deposit is not None:
            if withdrawal and float(withdrawal) > 0:
                return TransactionType.DEBIT
            if deposit and float(deposit) > 0:
                return TransactionType.CREDIT
        
        # Check amount sign
        if amount is not None:
            if amount < 0:
                return TransactionType.DEBIT
            elif amount > 0:
                return TransactionType.CREDIT
        
        # Check description for keywords
        if description:
            desc_upper = description.upper()
            
            debit_keywords = [
                'DEBIT', 'WITHDRAWAL', 'PURCHASE', 'PAYMENT', 'PAID',
                'TRANSFER TO', 'SENT TO', 'EMI', 'AUTOPAY', 'BILL PAY',
                'ATM WDL', 'POS', 'ECOM'
            ]
            
            credit_keywords = [
                'CREDIT', 'DEPOSIT', 'REFUND', 'CASHBACK', 'REVERSAL',
                'TRANSFER FROM', 'RECEIVED', 'SALARY', 'INTEREST',
                'DIVIDEND', 'BY TRANSFER'
            ]
            
            for keyword in debit_keywords:
                if keyword in desc_upper:
                    return TransactionType.DEBIT
            
            for keyword in credit_keywords:
                if keyword in desc_upper:
                    return TransactionType.CREDIT
        
        return TransactionType.UNKNOWN
    
    def detect_duplicate(
        self,
        t1: ParsedTransaction,
        t2: ParsedTransaction,
        date_tolerance_days: int = 0,
        amount_tolerance: float = 0.01
    ) -> bool:
        """
        Detect if two transactions are likely duplicates.
        
        Checks:
        - Same date (within tolerance)
        - Same amount (within tolerance)
        - Similar description
        
        Args:
            t1: First transaction
            t2: Second transaction
            date_tolerance_days: Days of tolerance for date matching
            amount_tolerance: Tolerance for amount matching
            
        Returns:
            True if likely duplicates
        """
        # Check date
        try:
            d1 = datetime.strptime(t1.date, "%Y-%m-%d")
            d2 = datetime.strptime(t2.date, "%Y-%m-%d")
            if abs((d1 - d2).days) > date_tolerance_days:
                return False
        except ValueError:
            return False
        
        # Check amount
        if abs(t1.amount - t2.amount) > amount_tolerance:
            return False
        
        # Check transaction type
        if t1.transaction_type != t2.transaction_type:
            return False
        
        # Check description similarity
        desc_similarity = SequenceMatcher(
            None,
            t1.description.lower(),
            t2.description.lower()
        ).ratio()
        
        if desc_similarity > 0.8:
            return True
        
        # Check if references match
        if t1.reference and t2.reference:
            if t1.reference == t2.reference:
                return True
        
        return False
    
    def remove_duplicates(
        self,
        transactions: List[ParsedTransaction],
        date_tolerance_days: int = 0
    ) -> Tuple[List[ParsedTransaction], List[ParsedTransaction]]:
        """
        Remove duplicate transactions from a list.
        
        Args:
            transactions: List of transactions
            date_tolerance_days: Days of tolerance for date matching
            
        Returns:
            Tuple of (unique transactions, removed duplicates)
        """
        if not transactions:
            return [], []
        
        unique = []
        duplicates = []
        
        for txn in transactions:
            is_dup = False
            for existing in unique:
                if self.detect_duplicate(txn, existing, date_tolerance_days):
                    is_dup = True
                    duplicates.append(txn)
                    break
            
            if not is_dup:
                unique.append(txn)
        
        return unique, duplicates
    
    def normalize_bank_name(self, bank_text: str) -> Optional[str]:
        """
        Normalize bank name to standard format.
        
        Args:
            bank_text: Raw bank name text
            
        Returns:
            Normalized bank name or None
        """
        if not bank_text:
            return None
        
        bank_text = bank_text.upper().strip()
        
        bank_mappings = {
            'HDFC': ['HDFC BANK', 'HDFCBANK', 'HDFC'],
            'SBI': ['STATE BANK OF INDIA', 'SBI', 'SBIN'],
            'ICICI': ['ICICI BANK', 'ICICIBANK', 'ICICI'],
            'AXIS': ['AXIS BANK', 'AXISBANK', 'AXIS'],
            'KOTAK': ['KOTAK MAHINDRA', 'KOTAK BANK', 'KOTAK'],
            'IDFC FIRST': ['IDFC FIRST', 'IDFC BANK', 'IDFCFIRST', 'IDFC'],
            'YES': ['YES BANK', 'YESBANK', 'YES'],
            'STANDARD CHARTERED': ['STANDARD CHARTERED', 'SCB'],
            'CITIBANK': ['CITIBANK', 'CITI BANK', 'CITI'],
            'PNB': ['PUNJAB NATIONAL BANK', 'PNB'],
            'BANK OF BARODA': ['BANK OF BARODA', 'BOB'],
            'CANARA': ['CANARA BANK', 'CANARA'],
            'UNION': ['UNION BANK', 'UNION'],
            'INDIAN': ['INDIAN BANK', 'INDIAN'],
            'INDUSIND': ['INDUSIND BANK', 'INDUSIND'],
            'FEDERAL': ['FEDERAL BANK', 'FEDERAL'],
            'RBL': ['RBL BANK', 'RATNAKAR BANK', 'RBL'],
            'BANDHAN': ['BANDHAN BANK', 'BANDHAN'],
        }
        
        for normalized, patterns in bank_mappings.items():
            for pattern in patterns:
                if pattern in bank_text:
                    return normalized
        
        return bank_text
    
    def mask_account_number(self, account_number: str) -> str:
        """
        Mask account number showing only last 4 digits.
        
        Args:
            account_number: Full account number
            
        Returns:
            Masked account number (XXXX-XXXX-1234)
        """
        if not account_number:
            return ""
        
        # Remove non-digit characters
        digits = re.sub(r'\D', '', str(account_number))
        
        if len(digits) < 4:
            return "XXXX"
        
        # Show only last 4 digits
        return f"XXXX-XXXX-{digits[-4:]}"
    
    def extract_account_number(self, text: str) -> Optional[str]:
        """
        Extract account number from text.
        
        Args:
            text: Text containing account number
            
        Returns:
            Account number or None
        """
        if not text:
            return None
        
        patterns = [
            r'A/C\s*(?:NO\.?)?\s*[:.]?\s*(\d{9,18})',
            r'ACCOUNT\s*(?:NO\.?|NUMBER)?\s*[:.]?\s*(\d{9,18})',
            r'ACCT\s*(?:NO\.?)?\s*[:.]?\s*(\d{9,18})',
            r'(\d{9,18})',  # Fallback: any long number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None


class TransactionCategorizer:
    """
    Auto-categorize transactions based on description.
    """
    
    # Category patterns
    CATEGORY_PATTERNS = {
        'Food & Dining': [
            r'SWIGGY', r'ZOMATO', r'RESTAURANT', r'CAFE', r'FOOD',
            r'DOMINOS', r'PIZZA', r'BURGER', r'MCDONALDS', r'KFC',
            r'STARBUCKS', r'CHAAYOS', r'HOTEL',
        ],
        'Shopping': [
            r'AMAZON', r'FLIPKART', r'MYNTRA', r'AJIO', r'NYKAA',
            r'SHOPPING', r'MALL', r'STORE', r'RETAIL',
        ],
        'Transport': [
            r'UBER', r'OLA', r'RAPIDO', r'METRO', r'RAILWAY', r'IRCTC',
            r'PETROL', r'FUEL', r'PARKING', r'TOLL',
        ],
        'Groceries': [
            r'BIGBASKET', r'BLINKIT', r'GROFERS', r'ZEPTO', r'INSTAMART',
            r'DMART', r'GROCERY', r'SUPERMARKET',
        ],
        'Utilities': [
            r'ELECTRICITY', r'WATER', r'GAS', r'INTERNET', r'BROADBAND',
            r'MOBILE', r'RECHARGE', r'BILL\s*PAY', r'AIRTEL', r'JIO', r'VI',
        ],
        'Entertainment': [
            r'NETFLIX', r'SPOTIFY', r'HOTSTAR', r'PRIME', r'YOUTUBE',
            r'MOVIE', r'PVR', r'INOX', r'CINEMA', r'GAMING',
        ],
        'Healthcare': [
            r'HOSPITAL', r'CLINIC', r'PHARMACY', r'MEDICAL', r'HEALTH',
            r'DOCTOR', r'APOLLO', r'MEDPLUS', r'NETMEDS',
        ],
        'Education': [
            r'SCHOOL', r'COLLEGE', r'UNIVERSITY', r'COURSE', r'UDEMY',
            r'COURSERA', r'EDUCATION', r'TUITION', r'BOOKS',
        ],
        'Investment': [
            r'ZERODHA', r'GROWW', r'UPSTOX', r'MUTUAL\s*FUND', r'SIP',
            r'STOCKS', r'TRADING', r'INVESTMENT',
        ],
        'Insurance': [
            r'INSURANCE', r'LIC', r'POLICY', r'PREMIUM',
        ],
        'EMI': [
            r'EMI', r'LOAN', r'BAJAJ\s*FIN', r'HDFC\s*LTD',
        ],
        'Transfer': [
            r'TRANSFER', r'NEFT', r'RTGS', r'IMPS', r'UPI',
        ],
        'Salary': [
            r'SALARY', r'PAYROLL', r'WAGES',
        ],
        'ATM': [
            r'ATM', r'CASH\s*WITHDRAWAL', r'CASH\s*WDL',
        ],
        'Rent': [
            r'RENT', r'HOUSING', r'LEASE',
        ],
    }
    
    def categorize(self, description: str) -> Optional[str]:
        """
        Categorize a transaction based on its description.
        
        Args:
            description: Transaction description
            
        Returns:
            Category name or None
        """
        if not description:
            return None
        
        desc_upper = description.upper()
        
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, desc_upper, re.IGNORECASE):
                    return category
        
        return 'Other'
    
    def batch_categorize(
        self,
        transactions: List[ParsedTransaction]
    ) -> List[ParsedTransaction]:
        """
        Categorize multiple transactions.
        
        Args:
            transactions: List of transactions
            
        Returns:
            Transactions with categories assigned
        """
        for txn in transactions:
            if not txn.category:
                txn.category = self.categorize(txn.description)
        
        return transactions
