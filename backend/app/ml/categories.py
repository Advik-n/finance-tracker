"""
Category Definitions for Financial Transactions.

This module defines the complete category hierarchy used for transaction
categorization in the Indian personal finance context.

Features:
- Hierarchical category structure with subcategories
- Indian-specific financial categories
- Visual elements (icons, colors) for UI
- Category metadata and attributes
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class CategoryType(str, Enum):
    """Main category types."""
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"
    INVESTMENT = "investment"


@dataclass
class CategoryDefinition:
    """Definition of a category with its properties."""
    name: str
    subcategories: List[str]
    icon: str
    color: str
    category_type: CategoryType = CategoryType.EXPENSE
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    priority: int = 0  # Higher priority categories are checked first
    tax_deductible: bool = False


# Complete category hierarchy for Indian users
CATEGORY_HIERARCHY: Dict[str, CategoryDefinition] = {
    "Housing": CategoryDefinition(
        name="Housing",
        subcategories=[
            "Rent",
            "Maintenance",
            "Property Tax",
            "Home Repairs",
            "Home Insurance",
            "Society Charges",
            "Water Tank",
            "Security"
        ],
        icon="🏠",
        color="#4A90D9",
        description="Housing and accommodation related expenses",
        keywords=["rent", "maintenance", "society", "housing", "home"],
        priority=90,
        tax_deductible=True  # HRA benefits
    ),
    
    "Utilities": CategoryDefinition(
        name="Utilities",
        subcategories=[
            "Electricity",
            "Water",
            "Piped Gas",
            "LPG Cylinder",
            "Internet",
            "Mobile Recharge",
            "DTH/Cable",
            "Landline"
        ],
        icon="💡",
        color="#F5A623",
        description="Utility bills and services",
        keywords=["electricity", "water", "gas", "internet", "mobile", "recharge", "bill"],
        priority=85
    ),
    
    "Transport": CategoryDefinition(
        name="Transport",
        subcategories=[
            "Petrol",
            "Diesel",
            "CNG",
            "Cab/Auto",
            "Public Transport",
            "Metro",
            "Vehicle Maintenance",
            "Vehicle Insurance",
            "Parking",
            "Toll",
            "FASTag",
            "Vehicle EMI"
        ],
        icon="🚗",
        color="#7ED321",
        description="Transportation and commute expenses",
        keywords=["petrol", "diesel", "cab", "uber", "ola", "auto", "bus", "metro", "parking", "toll"],
        priority=80
    ),
    
    "Food & Dining": CategoryDefinition(
        name="Food & Dining",
        subcategories=[
            "Groceries",
            "Ration",
            "Vegetables/Fruits",
            "Fast Food",
            "Restaurants",
            "Coffee/Tea",
            "Beverages",
            "Food Delivery",
            "Street Food",
            "Bakery",
            "Sweets/Mithai"
        ],
        icon="🍔",
        color="#D0021B",
        description="Food, groceries and dining expenses",
        keywords=["food", "grocery", "restaurant", "swiggy", "zomato", "dining", "cafe"],
        priority=75
    ),
    
    "Shopping": CategoryDefinition(
        name="Shopping",
        subcategories=[
            "Clothes/Apparel",
            "Footwear",
            "Electronics",
            "Home Appliances",
            "Furniture",
            "Kitchen Items",
            "Home Decor",
            "Personal Care",
            "Cosmetics",
            "Jewelry",
            "Accessories"
        ],
        icon="🛍️",
        color="#9013FE",
        description="Shopping and retail purchases",
        keywords=["shopping", "clothes", "electronics", "amazon", "flipkart", "myntra"],
        priority=70
    ),
    
    "Healthcare": CategoryDefinition(
        name="Healthcare",
        subcategories=[
            "Doctor/Hospital",
            "Medicines",
            "Lab Tests",
            "Health Insurance",
            "Dental",
            "Eye Care",
            "Ayurveda/Homeopathy",
            "Gym/Fitness",
            "Yoga",
            "Mental Health"
        ],
        icon="🏥",
        color="#50E3C2",
        description="Healthcare and medical expenses",
        keywords=["hospital", "doctor", "medicine", "pharmacy", "health", "medical", "apollo"],
        priority=88,
        tax_deductible=True  # Section 80D
    ),
    
    "Entertainment": CategoryDefinition(
        name="Entertainment",
        subcategories=[
            "Movies/Cinema",
            "OTT Subscriptions",
            "Music Subscriptions",
            "Gaming",
            "Events/Concerts",
            "Sports",
            "Hobbies",
            "Books/Magazines",
            "Amusement Parks"
        ],
        icon="🎬",
        color="#BD10E0",
        description="Entertainment and leisure activities",
        keywords=["movie", "netflix", "prime", "hotstar", "spotify", "gaming", "entertainment"],
        priority=50
    ),
    
    "Financial": CategoryDefinition(
        name="Financial",
        subcategories=[
            "EMI Payment",
            "Loan Repayment",
            "Credit Card Bill",
            "Investment",
            "SIP",
            "Mutual Fund",
            "Fixed Deposit",
            "PPF",
            "NPS",
            "Stock Purchase",
            "Insurance Premium",
            "Tax Payment",
            "TDS",
            "GST",
            "Bank Charges",
            "Locker Rent"
        ],
        icon="💰",
        color="#417505",
        category_type=CategoryType.INVESTMENT,
        description="Financial services and investments",
        keywords=["emi", "loan", "investment", "sip", "mutual fund", "insurance", "tax"],
        priority=95,
        tax_deductible=True
    ),
    
    "Education": CategoryDefinition(
        name="Education",
        subcategories=[
            "School Fees",
            "College Fees",
            "Tuition",
            "Coaching",
            "Books/Stationery",
            "Online Courses",
            "Certifications",
            "Entrance Exams",
            "Skill Development"
        ],
        icon="📚",
        color="#8B572A",
        description="Education and learning expenses",
        keywords=["school", "college", "tuition", "course", "education", "coaching", "book"],
        priority=87,
        tax_deductible=True  # Section 80C for tuition
    ),
    
    "Travel": CategoryDefinition(
        name="Travel",
        subcategories=[
            "Flight",
            "Train",
            "Bus",
            "Hotel",
            "Homestay",
            "Trip Expenses",
            "Travel Insurance",
            "Visa Fees",
            "Passport",
            "Tour Package",
            "Local Transport"
        ],
        icon="✈️",
        color="#00A3E0",
        description="Travel and vacation expenses",
        keywords=["flight", "train", "irctc", "makemytrip", "hotel", "travel", "trip"],
        priority=60
    ),
    
    "Personal": CategoryDefinition(
        name="Personal",
        subcategories=[
            "Gifts",
            "Donations/Charity",
            "Religious",
            "Pooja Items",
            "Personal Care",
            "Salon/Spa",
            "Laundry",
            "Household Help",
            "Maid/Cook",
            "Driver",
            "Pet Care",
            "Miscellaneous"
        ],
        icon="👤",
        color="#9B9B9B",
        description="Personal and miscellaneous expenses",
        keywords=["gift", "donation", "personal", "salon", "maid", "cook", "driver"],
        priority=40,
        tax_deductible=True  # Section 80G for donations
    ),
    
    "Family": CategoryDefinition(
        name="Family",
        subcategories=[
            "Kids Expenses",
            "School Bus",
            "Childcare",
            "Elderly Care",
            "Family Support",
            "Wedding/Functions",
            "Festival Expenses"
        ],
        icon="👨‍👩‍👧‍👦",
        color="#E74C3C",
        description="Family related expenses",
        keywords=["kids", "children", "wedding", "festival", "family", "function"],
        priority=55
    ),
    
    "Income": CategoryDefinition(
        name="Income",
        subcategories=[
            "Salary",
            "Bonus",
            "Freelance",
            "Business Income",
            "Interest Income",
            "Dividend",
            "Rental Income",
            "Capital Gains",
            "Refund",
            "Cashback",
            "Reimbursement",
            "Gift Received",
            "Other Income"
        ],
        icon="💵",
        color="#2ECC71",
        category_type=CategoryType.INCOME,
        description="Income and earnings",
        keywords=["salary", "income", "refund", "cashback", "bonus", "interest", "dividend"],
        priority=100
    ),
    
    "Transfer": CategoryDefinition(
        name="Transfer",
        subcategories=[
            "Self Transfer",
            "Account Transfer",
            "UPI Transfer",
            "NEFT/RTGS/IMPS",
            "Credit Card Payment",
            "Wallet Load",
            "Sent to Family",
            "Investment Transfer"
        ],
        icon="🔄",
        color="#95A5A6",
        category_type=CategoryType.TRANSFER,
        description="Money transfers between accounts",
        keywords=["transfer", "neft", "rtgs", "imps", "upi", "self"],
        priority=92
    ),
}


# Flat list of all categories for quick lookup
ALL_CATEGORIES: List[str] = list(CATEGORY_HIERARCHY.keys())

# Map subcategory to parent category
SUBCATEGORY_TO_CATEGORY: Dict[str, str] = {}
for category, definition in CATEGORY_HIERARCHY.items():
    for subcategory in definition.subcategories:
        SUBCATEGORY_TO_CATEGORY[subcategory] = category


def get_category_by_subcategory(subcategory: str) -> Optional[str]:
    """Get parent category for a given subcategory."""
    return SUBCATEGORY_TO_CATEGORY.get(subcategory)


def get_all_subcategories(category: str) -> List[str]:
    """Get all subcategories for a given category."""
    if category in CATEGORY_HIERARCHY:
        return CATEGORY_HIERARCHY[category].subcategories
    return []


def get_category_definition(category: str) -> Optional[CategoryDefinition]:
    """Get the full definition for a category."""
    return CATEGORY_HIERARCHY.get(category)


def get_tax_deductible_categories() -> List[str]:
    """Get list of tax-deductible categories."""
    return [
        category for category, definition in CATEGORY_HIERARCHY.items()
        if definition.tax_deductible
    ]


def get_categories_by_type(category_type: CategoryType) -> List[str]:
    """Get all categories of a specific type."""
    return [
        category for category, definition in CATEGORY_HIERARCHY.items()
        if definition.category_type == category_type
    ]


def get_expense_categories() -> List[str]:
    """Get all expense categories."""
    return get_categories_by_type(CategoryType.EXPENSE)


def get_income_subcategories() -> List[str]:
    """Get all income subcategories."""
    return CATEGORY_HIERARCHY["Income"].subcategories


# Indian average spending benchmarks by user type
INDIAN_AVERAGE_SPENDING: Dict[str, Dict[str, int]] = {
    "student": {
        "Housing": 8000,  # Hostel/PG
        "Utilities": 1500,
        "Transport": 2000,
        "Food & Dining": 6000,
        "Shopping": 2000,
        "Healthcare": 500,
        "Entertainment": 1500,
        "Education": 5000,
        "Personal": 1000,
    },
    "young_professional": {
        "Housing": 15000,
        "Utilities": 3000,
        "Transport": 4000,
        "Food & Dining": 8000,
        "Shopping": 4000,
        "Healthcare": 1500,
        "Entertainment": 3000,
        "Financial": 5000,
        "Education": 2000,
        "Travel": 3000,
        "Personal": 2000,
    },
    "professional": {
        "Housing": 20000,
        "Utilities": 4000,
        "Transport": 6000,
        "Food & Dining": 12000,
        "Shopping": 6000,
        "Healthcare": 3000,
        "Entertainment": 4000,
        "Financial": 15000,
        "Education": 3000,
        "Travel": 5000,
        "Personal": 3000,
    },
    "family_single_income": {
        "Housing": 25000,
        "Utilities": 5000,
        "Transport": 8000,
        "Food & Dining": 15000,
        "Shopping": 5000,
        "Healthcare": 5000,
        "Entertainment": 3000,
        "Financial": 20000,
        "Education": 15000,
        "Family": 5000,
        "Travel": 4000,
        "Personal": 4000,
    },
    "family_dual_income": {
        "Housing": 30000,
        "Utilities": 6000,
        "Transport": 12000,
        "Food & Dining": 18000,
        "Shopping": 8000,
        "Healthcare": 6000,
        "Entertainment": 5000,
        "Financial": 30000,
        "Education": 20000,
        "Family": 8000,
        "Travel": 8000,
        "Personal": 5000,
    },
    "senior_citizen": {
        "Housing": 15000,
        "Utilities": 4000,
        "Transport": 3000,
        "Food & Dining": 10000,
        "Shopping": 3000,
        "Healthcare": 10000,
        "Entertainment": 2000,
        "Financial": 5000,
        "Personal": 5000,
        "Family": 10000,
    },
}


# Subcategory-level benchmarks
SUBCATEGORY_BENCHMARKS: Dict[str, Dict[str, int]] = {
    "student": {
        "Petrol": 1500,
        "Public Transport": 500,
        "Groceries": 2000,
        "Fast Food": 2500,
        "Food Delivery": 1500,
        "Mobile Recharge": 500,
        "Internet": 500,
        "OTT Subscriptions": 500,
        "Clothes/Apparel": 1500,
    },
    "professional": {
        "Petrol": 4000,
        "Cab/Auto": 2000,
        "Groceries": 5000,
        "Fast Food": 3000,
        "Restaurants": 4000,
        "Food Delivery": 2500,
        "Electricity": 2000,
        "Mobile Recharge": 1000,
        "Internet": 1500,
        "OTT Subscriptions": 1000,
        "Gym/Fitness": 2000,
        "Clothes/Apparel": 3000,
        "EMI Payment": 10000,
        "SIP": 5000,
    },
    "family": {
        "Petrol": 6000,
        "Groceries": 10000,
        "Ration": 3000,
        "Vegetables/Fruits": 2000,
        "Fast Food": 2000,
        "Restaurants": 3000,
        "Food Delivery": 2000,
        "Electricity": 3000,
        "Piped Gas": 800,
        "LPG Cylinder": 1200,
        "Mobile Recharge": 2000,
        "Internet": 1500,
        "School Fees": 10000,
        "School Bus": 2000,
        "Tuition": 3000,
        "Medicines": 2000,
        "Maid/Cook": 5000,
        "EMI Payment": 15000,
        "SIP": 10000,
        "Insurance Premium": 5000,
    },
}


def get_benchmark_for_user_type(
    user_type: str,
    category: Optional[str] = None,
    subcategory: Optional[str] = None
) -> Optional[int]:
    """
    Get spending benchmark for a user type.
    
    Args:
        user_type: One of 'student', 'young_professional', 'professional',
                   'family_single_income', 'family_dual_income', 'senior_citizen'
        category: Optional category name
        subcategory: Optional subcategory name (takes precedence over category)
    
    Returns:
        Benchmark amount in INR or None if not found
    """
    if subcategory:
        # Map to simplified user type for subcategory benchmarks
        simplified_type = user_type
        if user_type in ["young_professional"]:
            simplified_type = "professional"
        elif user_type in ["family_single_income", "family_dual_income"]:
            simplified_type = "family"
        
        if simplified_type in SUBCATEGORY_BENCHMARKS:
            return SUBCATEGORY_BENCHMARKS[simplified_type].get(subcategory)
    
    if category:
        if user_type in INDIAN_AVERAGE_SPENDING:
            return INDIAN_AVERAGE_SPENDING[user_type].get(category)
    
    return None


# Category-wise recommended budget percentages (of net income)
BUDGET_PERCENTAGES: Dict[str, Dict[str, float]] = {
    "50_30_20_rule": {
        "needs": 0.50,  # Housing, Utilities, Transport, Groceries, Healthcare
        "wants": 0.30,  # Entertainment, Shopping, Dining out
        "savings": 0.20,  # Savings and investments
    },
    "detailed": {
        "Housing": 0.25,
        "Utilities": 0.05,
        "Transport": 0.10,
        "Food & Dining": 0.15,
        "Healthcare": 0.05,
        "Entertainment": 0.05,
        "Shopping": 0.05,
        "Education": 0.05,
        "Financial": 0.20,  # EMIs, Insurance, Savings
        "Personal": 0.03,
        "Travel": 0.02,
    },
}


def get_recommended_budget(net_income: float, budget_rule: str = "detailed") -> Dict[str, float]:
    """
    Calculate recommended budget based on income and budget rule.
    
    Args:
        net_income: Monthly net income in INR
        budget_rule: Either '50_30_20_rule' or 'detailed'
    
    Returns:
        Dictionary with category/type and recommended amount
    """
    if budget_rule not in BUDGET_PERCENTAGES:
        budget_rule = "detailed"
    
    percentages = BUDGET_PERCENTAGES[budget_rule]
    return {
        category: round(net_income * percentage, 2)
        for category, percentage in percentages.items()
    }
