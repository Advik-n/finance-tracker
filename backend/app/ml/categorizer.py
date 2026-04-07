"""
Transaction Categorizer Module.

This module provides ML-based transaction categorization with multiple
fallback strategies for accurate classification of financial transactions.

Features:
- Multi-stage categorization pipeline
- Exact and fuzzy merchant matching
- ML classification with scikit-learn
- Amount-based heuristics
- Time-based pattern recognition
- User feedback learning
"""

import re
import pickle
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from uuid import UUID

import numpy as np

from app.ml.merchant_dict import (
    MerchantDictionary,
    MerchantEntry,
    COMPILED_BANK_PATTERNS,
    BANK_PATTERNS,
)
from app.ml.categories import (
    CATEGORY_HIERARCHY,
    CategoryDefinition,
    get_category_by_subcategory,
    get_all_subcategories,
)

logger = logging.getLogger(__name__)


class CategorizationMethod(str, Enum):
    """How the category was determined."""
    EXACT_MATCH = "exact_match"
    FUZZY_MATCH = "fuzzy_match"
    UPI_MATCH = "upi_match"
    PATTERN_MATCH = "pattern_match"
    ML_CLASSIFICATION = "ml_classification"
    AMOUNT_HEURISTIC = "amount_heuristic"
    TIME_PATTERN = "time_pattern"
    USER_CORRECTION = "user_correction"
    KEYWORD_MATCH = "keyword_match"
    DEFAULT = "default"


@dataclass
class CategoryResult:
    """Result of transaction categorization."""
    category: str
    subcategory: str
    confidence: float
    method: CategorizationMethod
    merchant_name: Optional[str] = None
    is_subscription: bool = False
    is_recurring: bool = False
    alternative_categories: List[Tuple[str, str, float]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "confidence": round(self.confidence, 3),
            "method": self.method.value,
            "merchant_name": self.merchant_name,
            "is_subscription": self.is_subscription,
            "is_recurring": self.is_recurring,
            "alternative_categories": [
                {"category": c, "subcategory": s, "confidence": round(conf, 3)}
                for c, s, conf in self.alternative_categories
            ],
            "metadata": self.metadata,
        }


@dataclass
class TransactionInput:
    """Input transaction data for categorization."""
    description: str
    amount: float
    transaction_type: str  # 'credit' or 'debit'
    date: datetime
    bank_name: Optional[str] = None
    upi_id: Optional[str] = None
    reference_number: Optional[str] = None
    balance: Optional[float] = None
    user_id: Optional[str] = None


class TextProcessor:
    """Process and normalize transaction descriptions."""
    
    # Common noise words to remove
    NOISE_WORDS = {
        "pvt", "ltd", "private", "limited", "india", "inr",
        "debit", "credit", "card", "payment", "transaction",
        "ref", "no", "number", "acc", "account", "bank",
        "international", "domestic", "online", "pos", "ecom",
        "request", "successful", "completed", "approved",
    }
    
    # Patterns to clean
    CLEAN_PATTERNS = [
        (r'\d{4}[Xx*]{4,}\d{4}', ''),  # Masked card numbers
        (r'\d{10,}', ''),  # Long numbers (account numbers, etc.)
        (r'[A-Z]{2,3}\d{10,}', ''),  # Reference numbers like IMPS123456789
        (r'VPA:\s*\S+', ''),  # VPA addresses
        (r'REF\s*:\s*\S+', ''),  # Reference markers
        (r'UPI/\d+/', ''),  # UPI transaction IDs
        (r'IMPS/\d+/', ''),  # IMPS transaction IDs
        (r'NEFT/\d+/', ''),  # NEFT transaction IDs
        (r'\d{2}/\d{2}/\d{2,4}', ''),  # Dates
        (r'\d{2}:\d{2}(:\d{2})?', ''),  # Times
        (r'INR\s*[\d,\.]+', ''),  # Amount patterns
        (r'RS\.?\s*[\d,\.]+', ''),  # Rupee amounts
        (r'@[a-z0-9]+', ''),  # UPI handles (keep separately)
    ]
    
    @classmethod
    def normalize(cls, text: str) -> str:
        """
        Normalize transaction description text.
        
        Args:
            text: Raw transaction description
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Apply cleaning patterns
        for pattern, replacement in cls.CLEAN_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    @classmethod
    def extract_keywords(cls, text: str) -> List[str]:
        """
        Extract meaningful keywords from description.
        
        Args:
            text: Transaction description
            
        Returns:
            List of keywords
        """
        normalized = cls.normalize(text)
        
        # Split into words
        words = re.findall(r'[a-z]+', normalized)
        
        # Filter noise words and short words
        keywords = [
            w for w in words
            if w not in cls.NOISE_WORDS and len(w) > 2
        ]
        
        return keywords
    
    @classmethod
    def extract_upi_id(cls, text: str) -> Optional[str]:
        """Extract UPI ID from transaction description."""
        # Pattern for UPI IDs
        upi_patterns = [
            r'([a-z0-9._-]+@[a-z]+)',  # standard@bank format
            r'VPA[:\s]+([a-z0-9._-]+@[a-z]+)',  # VPA: prefix
            r'to\s+([a-z0-9._-]+@[a-z]+)',  # "to" prefix
        ]
        
        text_lower = text.lower()
        for pattern in upi_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1)
        
        return None
    
    @classmethod
    def extract_merchant_name(cls, text: str) -> Optional[str]:
        """
        Extract likely merchant name from description.
        
        Uses NLP-like heuristics to identify the merchant.
        """
        normalized = cls.normalize(text)
        
        # Common patterns where merchant name appears
        patterns = [
            r'(?:to|at|from)\s+([a-z][a-z\s]{2,30}?)(?:\s+(?:ref|upi|imps|neft|via|for)|$)',
            r'pos\s+(?:\d+\s+)?([a-z][a-z\s]{2,30})',
            r'(?:upi|imps|neft)[/-]?[a-z]*[/-]([a-z][a-z\s]{2,25})',
            r'^([a-z][a-z\s]{2,25})(?:\s+(?:payment|purchase|bill|recharge))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                merchant = match.group(1).strip()
                # Clean up and validate
                merchant = ' '.join(merchant.split())
                if len(merchant) >= 3 and not merchant.isdigit():
                    return merchant.title()
        
        # Fallback: Use first meaningful phrase
        keywords = cls.extract_keywords(text)
        if keywords and len(keywords[0]) >= 3:
            return keywords[0].title()
        
        return None


class AmountHeuristics:
    """
    Amount-based categorization heuristics.
    
    Uses typical transaction amount ranges to suggest categories.
    """
    
    # Amount ranges for different categories (min, max, category, subcategory, confidence)
    AMOUNT_RANGES: List[Tuple[float, float, str, str, float]] = [
        # Very small amounts - likely food/beverage
        (10, 100, "Food & Dining", "Street Food", 0.4),
        (10, 100, "Food & Dining", "Coffee/Tea", 0.4),
        
        # Small amounts - utilities/recharge
        (100, 500, "Utilities", "Mobile Recharge", 0.35),
        (30, 200, "Transport", "Metro", 0.35),
        (50, 500, "Transport", "Cab/Auto", 0.35),
        
        # Medium amounts - food delivery, groceries
        (200, 1500, "Food & Dining", "Food Delivery", 0.30),
        (500, 5000, "Food & Dining", "Groceries", 0.30),
        
        # Fuel amounts
        (500, 5000, "Transport", "Petrol", 0.35),
        
        # Utility bills
        (500, 10000, "Utilities", "Electricity", 0.30),
        
        # OTT subscriptions
        (149, 700, "Entertainment", "OTT Subscriptions", 0.40),
        
        # Rent range
        (10000, 100000, "Housing", "Rent", 0.30),
        
        # Large amounts - EMI, Investment
        (5000, 100000, "Financial", "EMI Payment", 0.25),
        (1000, 500000, "Financial", "Investment", 0.25),
    ]
    
    @classmethod
    def get_suggestions(cls, amount: float, is_debit: bool = True) -> List[Tuple[str, str, float]]:
        """
        Get category suggestions based on amount.
        
        Args:
            amount: Transaction amount
            is_debit: Whether this is a debit transaction
            
        Returns:
            List of (category, subcategory, confidence) suggestions
        """
        if not is_debit:
            # Credits are usually income
            if amount >= 20000:
                return [("Income", "Salary", 0.50)]
            elif amount >= 100:
                return [
                    ("Income", "Other Income", 0.30),
                    ("Income", "Refund", 0.25),
                    ("Income", "Cashback", 0.20),
                ]
            return []
        
        suggestions = []
        for min_amt, max_amt, category, subcategory, confidence in cls.AMOUNT_RANGES:
            if min_amt <= amount <= max_amt:
                suggestions.append((category, subcategory, confidence))
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x[2], reverse=True)
        return suggestions[:5]  # Return top 5


class TimePatternAnalyzer:
    """
    Analyze time-based patterns in transactions.
    
    Identifies patterns like:
    - Weekend vs weekday spending
    - Monthly recurring transactions
    - Time-of-day patterns
    """
    
    @staticmethod
    def is_weekend(date: datetime) -> bool:
        """Check if date falls on weekend."""
        return date.weekday() >= 5
    
    @staticmethod
    def get_time_of_day(date: datetime) -> str:
        """Categorize time of day."""
        hour = date.hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    @staticmethod
    def get_day_of_month(date: datetime) -> int:
        """Get day of month."""
        return date.day
    
    @classmethod
    def get_time_hints(cls, date: datetime) -> Dict[str, Any]:
        """
        Get category hints based on transaction time.
        
        Args:
            date: Transaction datetime
            
        Returns:
            Dictionary with time-based hints
        """
        hints = {
            "is_weekend": cls.is_weekend(date),
            "time_of_day": cls.get_time_of_day(date),
            "day_of_month": cls.get_day_of_month(date),
            "category_hints": [],
        }
        
        # Weekend patterns
        if hints["is_weekend"]:
            hints["category_hints"].extend([
                ("Food & Dining", "Restaurants", 0.1),
                ("Entertainment", "Movies/Cinema", 0.1),
                ("Shopping", "Clothes/Apparel", 0.05),
            ])
        
        # Morning patterns
        if hints["time_of_day"] == "morning":
            hints["category_hints"].extend([
                ("Food & Dining", "Coffee/Tea", 0.1),
                ("Transport", "Cab/Auto", 0.1),
            ])
        
        # Evening patterns
        if hints["time_of_day"] == "evening":
            hints["category_hints"].extend([
                ("Food & Dining", "Food Delivery", 0.1),
                ("Food & Dining", "Restaurants", 0.1),
            ])
        
        # Month-start patterns (rent, salary)
        if hints["day_of_month"] <= 5:
            hints["category_hints"].extend([
                ("Housing", "Rent", 0.15),
                ("Income", "Salary", 0.15),
            ])
        
        # Month-end patterns
        if hints["day_of_month"] >= 25:
            hints["category_hints"].extend([
                ("Financial", "EMI Payment", 0.1),
                ("Financial", "Credit Card Bill", 0.1),
            ])
        
        return hints


class MLClassifier:
    """
    Machine Learning classifier for transaction categorization.
    
    Uses a pre-trained model or trains on user-corrected data.
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize the ML classifier.
        
        Args:
            model_path: Path to saved model file
        """
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.is_trained = False
        self.model_path = model_path
        
        if model_path and model_path.exists():
            self._load_model(model_path)
    
    def _load_model(self, path: Path) -> bool:
        """Load a saved model."""
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.vectorizer = data['vectorizer']
                self.label_encoder = data['label_encoder']
                self.is_trained = True
            logger.info(f"Loaded ML model from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def save_model(self, path: Path) -> bool:
        """Save the trained model."""
        if not self.is_trained:
            logger.warning("Cannot save untrained model")
            return False
        
        try:
            with open(path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'vectorizer': self.vectorizer,
                    'label_encoder': self.label_encoder,
                }, f)
            logger.info(f"Saved ML model to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    def train(self, transactions: List[Dict[str, Any]]) -> bool:
        """
        Train the classifier on labeled transactions.
        
        Args:
            transactions: List of transactions with 'description' and 'category' fields
            
        Returns:
            True if training was successful
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            from sklearn.preprocessing import LabelEncoder
            from sklearn.pipeline import Pipeline
            
            # Prepare training data
            descriptions = [
                TextProcessor.normalize(t['description'])
                for t in transactions
            ]
            labels = [f"{t['category']}|{t['subcategory']}" for t in transactions]
            
            if len(set(labels)) < 2:
                logger.warning("Not enough unique categories to train")
                return False
            
            # Create and train pipeline
            self.label_encoder = LabelEncoder()
            encoded_labels = self.label_encoder.fit_transform(labels)
            
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 3),
                min_df=2,
                max_df=0.95,
            )
            
            X = self.vectorizer.fit_transform(descriptions)
            
            self.model = MultinomialNB(alpha=0.1)
            self.model.fit(X, encoded_labels)
            
            self.is_trained = True
            logger.info(f"Trained ML model on {len(transactions)} transactions")
            return True
            
        except ImportError:
            logger.warning("scikit-learn not installed. ML classification disabled.")
            return False
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
    
    def predict(self, description: str) -> Optional[Tuple[str, str, float]]:
        """
        Predict category for a transaction description.
        
        Args:
            description: Transaction description
            
        Returns:
            Tuple of (category, subcategory, confidence) or None
        """
        if not self.is_trained:
            return None
        
        try:
            normalized = TextProcessor.normalize(description)
            X = self.vectorizer.transform([normalized])
            
            # Get prediction and probability
            proba = self.model.predict_proba(X)[0]
            max_idx = proba.argmax()
            confidence = proba[max_idx]
            
            # Decode label
            label = self.label_encoder.inverse_transform([max_idx])[0]
            category, subcategory = label.split('|')
            
            return (category, subcategory, confidence)
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None
    
    def predict_top_n(
        self,
        description: str,
        n: int = 3
    ) -> List[Tuple[str, str, float]]:
        """
        Get top N predictions with probabilities.
        
        Args:
            description: Transaction description
            n: Number of predictions to return
            
        Returns:
            List of (category, subcategory, confidence) tuples
        """
        if not self.is_trained:
            return []
        
        try:
            normalized = TextProcessor.normalize(description)
            X = self.vectorizer.transform([normalized])
            
            proba = self.model.predict_proba(X)[0]
            top_indices = proba.argsort()[-n:][::-1]
            
            results = []
            for idx in top_indices:
                confidence = proba[idx]
                if confidence > 0.01:  # Minimum threshold
                    label = self.label_encoder.inverse_transform([idx])[0]
                    category, subcategory = label.split('|')
                    results.append((category, subcategory, confidence))
            
            return results
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return []


class TransactionCategorizer:
    """
    Main transaction categorizer with multi-stage classification pipeline.
    
    Pipeline stages:
    1. Bank pattern matching (UPI, NEFT, IMPS patterns)
    2. Exact merchant match from dictionary
    3. UPI ID matching
    4. Fuzzy merchant match (Levenshtein distance)
    5. ML classification
    6. Amount-based heuristics
    7. Time-based patterns
    8. Default categorization
    """
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        confidence_threshold: float = 0.5
    ):
        """
        Initialize the categorizer.
        
        Args:
            model_path: Path to saved ML model
            confidence_threshold: Minimum confidence for accepting a category
        """
        self.merchant_dict = MerchantDictionary()
        self.ml_classifier = MLClassifier(model_path)
        self.confidence_threshold = confidence_threshold
        
        # User correction history for learning
        self.corrections: Dict[str, Tuple[str, str]] = {}
        
        logger.info(f"Initialized categorizer with {self.merchant_dict.get_statistics()}")
    
    def categorize(self, transaction: TransactionInput) -> CategoryResult:
        """
        Categorize a transaction using the multi-stage pipeline.
        
        Args:
            transaction: Input transaction data
            
        Returns:
            CategoryResult with category, confidence, and metadata
        """
        description = transaction.description
        normalized = TextProcessor.normalize(description)
        is_debit = transaction.transaction_type.lower() == 'debit'
        
        # Collect all candidates from different methods
        candidates: List[Tuple[str, str, float, CategorizationMethod, Optional[str]]] = []
        
        # Stage 1: Bank pattern matching
        bank_result = self._match_bank_patterns(description)
        if bank_result:
            candidates.append(bank_result)
        
        # Stage 2: Check for user corrections (highest priority)
        correction_key = f"{normalized}:{transaction.amount}"
        if correction_key in self.corrections:
            cat, subcat = self.corrections[correction_key]
            candidates.append((cat, subcat, 0.99, CategorizationMethod.USER_CORRECTION, None))
        
        # Stage 3: UPI ID matching
        upi_id = transaction.upi_id or TextProcessor.extract_upi_id(description)
        if upi_id:
            upi_result = self._match_upi(upi_id)
            if upi_result:
                candidates.append(upi_result)
        
        # Stage 4: Exact merchant match
        exact_matches = self.merchant_dict.lookup_contains(normalized)
        for merchant, confidence in exact_matches[:3]:
            candidates.append((
                merchant.category,
                merchant.subcategory,
                confidence,
                CategorizationMethod.EXACT_MATCH,
                merchant.name
            ))
        
        # Stage 5: Fuzzy merchant match (if no exact match found)
        if not exact_matches:
            fuzzy_matches = self.merchant_dict.lookup_fuzzy(normalized, threshold=0.65)
            for merchant, similarity in fuzzy_matches[:2]:
                candidates.append((
                    merchant.category,
                    merchant.subcategory,
                    similarity * 0.8,  # Reduce confidence for fuzzy matches
                    CategorizationMethod.FUZZY_MATCH,
                    merchant.name
                ))
        
        # Stage 6: ML classification
        ml_result = self.ml_classifier.predict(normalized)
        if ml_result:
            cat, subcat, conf = ml_result
            candidates.append((cat, subcat, conf * 0.85, CategorizationMethod.ML_CLASSIFICATION, None))
        
        # Stage 7: Amount heuristics
        amount_hints = AmountHeuristics.get_suggestions(transaction.amount, is_debit)
        for cat, subcat, conf in amount_hints[:2]:
            candidates.append((cat, subcat, conf, CategorizationMethod.AMOUNT_HEURISTIC, None))
        
        # Stage 8: Time patterns
        time_hints = TimePatternAnalyzer.get_time_hints(transaction.date)
        for cat, subcat, conf in time_hints.get('category_hints', []):
            candidates.append((cat, subcat, conf, CategorizationMethod.TIME_PATTERN, None))
        
        # Select best candidate
        if candidates:
            # Sort by confidence
            candidates.sort(key=lambda x: x[2], reverse=True)
            best = candidates[0]
            
            # Build alternative categories
            alternatives = [
                (c[0], c[1], c[2])
                for c in candidates[1:5]
                if c[2] >= 0.1
            ]
            
            # Check if it's a subscription
            is_subscription = False
            merchant_name = best[4]
            if merchant_name:
                is_subscription = self.merchant_dict.is_subscription_merchant(merchant_name)
            
            return CategoryResult(
                category=best[0],
                subcategory=best[1],
                confidence=best[2],
                method=best[3],
                merchant_name=merchant_name,
                is_subscription=is_subscription,
                alternative_categories=alternatives,
                metadata={
                    "time_hints": time_hints,
                    "normalized_description": normalized,
                }
            )
        
        # Default fallback
        default_category = "Personal" if is_debit else "Income"
        default_subcategory = "Miscellaneous" if is_debit else "Other Income"
        
        return CategoryResult(
            category=default_category,
            subcategory=default_subcategory,
            confidence=0.1,
            method=CategorizationMethod.DEFAULT,
            metadata={
                "time_hints": TimePatternAnalyzer.get_time_hints(transaction.date),
                "normalized_description": normalized,
            }
        )
    
    def _match_bank_patterns(
        self,
        description: str
    ) -> Optional[Tuple[str, str, float, CategorizationMethod, Optional[str]]]:
        """Match bank transaction patterns."""
        for pattern_name, pattern_data in COMPILED_BANK_PATTERNS.items():
            for regex in pattern_data["regex"]:
                if regex.search(description):
                    return (
                        pattern_data["category"],
                        pattern_data["subcategory"],
                        0.80,
                        CategorizationMethod.PATTERN_MATCH,
                        None
                    )
        return None
    
    def _match_upi(
        self,
        upi_id: str
    ) -> Optional[Tuple[str, str, float, CategorizationMethod, Optional[str]]]:
        """Match UPI ID against merchant dictionary."""
        merchant = self.merchant_dict.lookup_upi(upi_id)
        if merchant:
            return (
                merchant.category,
                merchant.subcategory,
                0.90,
                CategorizationMethod.UPI_MATCH,
                merchant.name
            )
        return None
    
    def extract_merchant(self, description: str) -> Optional[str]:
        """
        Extract merchant name from transaction description.
        
        Args:
            description: Transaction description
            
        Returns:
            Extracted merchant name or None
        """
        # Try dictionary lookup first
        matches = self.merchant_dict.lookup_contains(description)
        if matches:
            return matches[0][0].name
        
        # Use text processing
        return TextProcessor.extract_merchant_name(description)
    
    def train_model(self, transactions: List[Dict[str, Any]]) -> bool:
        """
        Train the ML classifier on labeled transactions.
        
        Args:
            transactions: List of transactions with category labels
            
        Returns:
            True if training was successful
        """
        return self.ml_classifier.train(transactions)
    
    def record_correction(
        self,
        description: str,
        amount: float,
        correct_category: str,
        correct_subcategory: str
    ):
        """
        Record a user correction for future categorization.
        
        Args:
            description: Transaction description
            amount: Transaction amount
            correct_category: The correct category
            correct_subcategory: The correct subcategory
        """
        normalized = TextProcessor.normalize(description)
        key = f"{normalized}:{amount}"
        self.corrections[key] = (correct_category, correct_subcategory)
        logger.info(f"Recorded correction: '{description[:50]}...' -> {correct_category}/{correct_subcategory}")
    
    def batch_categorize(
        self,
        transactions: List[TransactionInput]
    ) -> List[CategoryResult]:
        """
        Categorize multiple transactions.
        
        Args:
            transactions: List of transaction inputs
            
        Returns:
            List of category results
        """
        return [self.categorize(t) for t in transactions]
    
    def get_category_suggestions(
        self,
        description: str,
        amount: float,
        transaction_type: str = "debit",
        top_n: int = 5
    ) -> List[Tuple[str, str, float]]:
        """
        Get category suggestions without committing to one.
        
        Useful for UI autocomplete or user selection.
        
        Args:
            description: Transaction description
            amount: Transaction amount
            transaction_type: 'credit' or 'debit'
            top_n: Number of suggestions to return
            
        Returns:
            List of (category, subcategory, confidence) suggestions
        """
        transaction = TransactionInput(
            description=description,
            amount=amount,
            transaction_type=transaction_type,
            date=datetime.now()
        )
        
        result = self.categorize(transaction)
        
        suggestions = [(result.category, result.subcategory, result.confidence)]
        suggestions.extend(result.alternative_categories)
        
        # De-duplicate and return top N
        seen = set()
        unique = []
        for cat, subcat, conf in suggestions:
            key = f"{cat}|{subcat}"
            if key not in seen:
                seen.add(key)
                unique.append((cat, subcat, conf))
        
        return unique[:top_n]
    
    # Legacy API compatibility
    def predict(
        self,
        description: str,
        merchant_name: Optional[str],
        amount: float,
        categories: List,
    ) -> Tuple[Optional[UUID], float]:
        """
        Legacy predict method for backward compatibility.
        
        Args:
            description: Transaction description
            merchant_name: Merchant name
            amount: Transaction amount
            categories: Available categories
            
        Returns:
            Tuple of (category_id, confidence_score)
        """
        if not categories:
            return None, 0.0
        
        # Use new categorization
        transaction = TransactionInput(
            description=f"{description} {merchant_name or ''}",
            amount=amount,
            transaction_type="debit",
            date=datetime.now()
        )
        
        result = self.categorize(transaction)
        
        # Map to legacy category format
        text = f"{description} {merchant_name or ''}".lower()
        
        # Try keyword matching first
        for category in categories:
            if hasattr(category, 'keywords') and category.keywords:
                keywords = [k.strip().lower() for k in category.keywords.split(",")]
                for keyword in keywords:
                    if keyword and keyword in text:
                        return category.id, 0.9
        
        # Try slug matching with our result
        for category in categories:
            if hasattr(category, 'slug'):
                if category.slug.lower() in result.category.lower():
                    return category.id, result.confidence
                if category.slug.lower() in result.subcategory.lower():
                    return category.id, result.confidence
        
        return None, 0.0
    
    def train(self, transactions: List[Dict]) -> None:
        """
        Legacy train method for backward compatibility.
        
        Args:
            transactions: List of categorized transactions for training
        """
        self.train_model(transactions)


# Singleton instance
_categorizer: Optional[TransactionCategorizer] = None


def get_categorizer() -> TransactionCategorizer:
    """Get or create the global categorizer instance."""
    global _categorizer
    if _categorizer is None:
        _categorizer = TransactionCategorizer()
    return _categorizer


def categorize_transaction(
    description: str,
    amount: float,
    transaction_type: str = "debit",
    date: Optional[datetime] = None,
    upi_id: Optional[str] = None,
) -> CategoryResult:
    """
    Convenience function to categorize a single transaction.
    
    Args:
        description: Transaction description
        amount: Transaction amount
        transaction_type: 'credit' or 'debit'
        date: Transaction date (defaults to now)
        upi_id: Optional UPI ID
        
    Returns:
        CategoryResult
    """
    categorizer = get_categorizer()
    
    transaction = TransactionInput(
        description=description,
        amount=amount,
        transaction_type=transaction_type,
        date=date or datetime.now(),
        upi_id=upi_id
    )
    
    return categorizer.categorize(transaction)
