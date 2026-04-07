"""
Comprehensive Indian Merchant Dictionary for Transaction Categorization.

This module contains an extensive database of Indian merchants, services,
and payment identifiers used to automatically categorize financial transactions.

Features:
- 200+ merchant entries covering major Indian businesses
- UPI identifiers and payment app patterns
- Bank-specific transaction patterns
- Category mapping with confidence scores
- Fuzzy matching support with keyword variations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import re


@dataclass
class MerchantEntry:
    """A merchant entry with categorization details."""
    name: str
    keywords: List[str]
    category: str
    subcategory: str
    aliases: List[str] = field(default_factory=list)
    upi_patterns: List[str] = field(default_factory=list)
    confidence: float = 0.95  # How confident we are in this mapping
    is_subscription: bool = False
    typical_amount_range: Optional[Tuple[int, int]] = None  # (min, max) in INR


# ============================================================================
# COMPREHENSIVE INDIAN MERCHANT DICTIONARY
# ============================================================================

MERCHANT_CATEGORIES: Dict[str, MerchantEntry] = {
    
    # ==========================================================================
    # FUEL & TRANSPORT - Petrol Pumps and Fuel Stations
    # ==========================================================================
    
    "indian_oil": MerchantEntry(
        name="Indian Oil Corporation",
        keywords=["indian oil", "iocl", "indane", "indianoil", "indian oil corp"],
        category="Transport",
        subcategory="Petrol",
        upi_patterns=["indianoil", "iocl"],
        typical_amount_range=(500, 5000)
    ),
    
    "hp_petroleum": MerchantEntry(
        name="Hindustan Petroleum",
        keywords=["hp petroleum", "hpcl", "hindustan petroleum", "hp petrol", "hp fuel"],
        category="Transport",
        subcategory="Petrol",
        upi_patterns=["hpcl", "hppetroleum"],
        typical_amount_range=(500, 5000)
    ),
    
    "bharat_petroleum": MerchantEntry(
        name="Bharat Petroleum",
        keywords=["bharat petroleum", "bpcl", "bp petrol", "bharatpetroleum"],
        category="Transport",
        subcategory="Petrol",
        upi_patterns=["bpcl", "bharatpetroleum"],
        typical_amount_range=(500, 5000)
    ),
    
    "reliance_petroleum": MerchantEntry(
        name="Reliance Petroleum",
        keywords=["reliance petroleum", "reliance petrol", "reliance fuel", "jio bp"],
        category="Transport",
        subcategory="Petrol",
        upi_patterns=["reliancepetroleum", "jiobp"],
        typical_amount_range=(500, 5000)
    ),
    
    "shell_india": MerchantEntry(
        name="Shell India",
        keywords=["shell", "shell india", "shell petrol", "shell fuel"],
        category="Transport",
        subcategory="Petrol",
        typical_amount_range=(500, 6000)
    ),
    
    "nayara_energy": MerchantEntry(
        name="Nayara Energy",
        keywords=["nayara", "nayara energy", "essar petrol", "essar fuel"],
        category="Transport",
        subcategory="Petrol",
        typical_amount_range=(500, 5000)
    ),
    
    "generic_petrol": MerchantEntry(
        name="Petrol Pump",
        keywords=["petrol pump", "petrol", "fuel station", "filling station", "diesel", "cng station"],
        category="Transport",
        subcategory="Petrol",
        confidence=0.85,
        typical_amount_range=(200, 5000)
    ),
    
    # ==========================================================================
    # RIDE HAILING & TRANSPORT SERVICES
    # ==========================================================================
    
    "ola": MerchantEntry(
        name="Ola Cabs",
        keywords=["ola", "ola cabs", "ola money", "olacabs", "ani technologies"],
        category="Transport",
        subcategory="Cab/Auto",
        upi_patterns=["olacabs", "olamoney", "ola@"],
        typical_amount_range=(50, 2000)
    ),
    
    "uber": MerchantEntry(
        name="Uber",
        keywords=["uber", "uber india", "uber cab", "uber eats"],
        category="Transport",
        subcategory="Cab/Auto",
        upi_patterns=["uber", "uberindia"],
        typical_amount_range=(50, 2000)
    ),
    
    "rapido": MerchantEntry(
        name="Rapido",
        keywords=["rapido", "rapido bike", "rapido auto"],
        category="Transport",
        subcategory="Cab/Auto",
        upi_patterns=["rapido"],
        typical_amount_range=(30, 500)
    ),
    
    "meru": MerchantEntry(
        name="Meru Cabs",
        keywords=["meru", "meru cabs"],
        category="Transport",
        subcategory="Cab/Auto",
        typical_amount_range=(100, 3000)
    ),
    
    "bluedart": MerchantEntry(
        name="Blue Dart",
        keywords=["blue dart", "bluedart", "dhl blue dart"],
        category="Shopping",
        subcategory="Personal Care",
        confidence=0.80,
        typical_amount_range=(50, 500)
    ),
    
    "fastag": MerchantEntry(
        name="FASTag",
        keywords=["fastag", "fas tag", "toll", "nhai", "netc fastag"],
        category="Transport",
        subcategory="Toll",
        upi_patterns=["fastag", "nhai"],
        typical_amount_range=(50, 500)
    ),
    
    "metro": MerchantEntry(
        name="Metro Rail",
        keywords=["metro", "dmrc", "bmrc", "cmrl", "mmrc", "metro rail", "delhi metro", "bangalore metro", "mumbai metro", "chennai metro", "hyderabad metro"],
        category="Transport",
        subcategory="Metro",
        upi_patterns=["dmrc", "bmrcl"],
        typical_amount_range=(20, 200)
    ),
    
    "irctc": MerchantEntry(
        name="IRCTC",
        keywords=["irctc", "indian railway", "railway ticket", "train ticket", "rail ticket"],
        category="Travel",
        subcategory="Train",
        upi_patterns=["irctc"],
        typical_amount_range=(100, 5000)
    ),
    
    # ==========================================================================
    # FOOD DELIVERY PLATFORMS
    # ==========================================================================
    
    "swiggy": MerchantEntry(
        name="Swiggy",
        keywords=["swiggy", "bundl technologies", "swiggy instamart", "swiggy genie", "swiggy dineout"],
        category="Food & Dining",
        subcategory="Food Delivery",
        upi_patterns=["swiggy", "bundl"],
        typical_amount_range=(100, 1500)
    ),
    
    "zomato": MerchantEntry(
        name="Zomato",
        keywords=["zomato", "zomato media", "zomato gold", "zomato pro", "blinkit", "hyperpure"],
        category="Food & Dining",
        subcategory="Food Delivery",
        upi_patterns=["zomato"],
        typical_amount_range=(100, 1500)
    ),
    
    "dunzo": MerchantEntry(
        name="Dunzo",
        keywords=["dunzo", "dunzo daily"],
        category="Food & Dining",
        subcategory="Food Delivery",
        upi_patterns=["dunzo"],
        typical_amount_range=(50, 1000)
    ),
    
    "eatsure": MerchantEntry(
        name="EatSure",
        keywords=["eatsure", "eat sure", "rebel foods"],
        category="Food & Dining",
        subcategory="Food Delivery",
        typical_amount_range=(150, 800)
    ),
    
    # ==========================================================================
    # QUICK COMMERCE & GROCERY
    # ==========================================================================
    
    "blinkit": MerchantEntry(
        name="Blinkit",
        keywords=["blinkit", "grofers", "blink it"],
        category="Food & Dining",
        subcategory="Groceries",
        upi_patterns=["blinkit", "grofers"],
        typical_amount_range=(100, 3000)
    ),
    
    "zepto": MerchantEntry(
        name="Zepto",
        keywords=["zepto", "zepto instant"],
        category="Food & Dining",
        subcategory="Groceries",
        upi_patterns=["zepto"],
        typical_amount_range=(100, 2000)
    ),
    
    "bigbasket": MerchantEntry(
        name="BigBasket",
        keywords=["bigbasket", "big basket", "bb instant", "bbnow", "supermarket grocery"],
        category="Food & Dining",
        subcategory="Groceries",
        upi_patterns=["bigbasket"],
        typical_amount_range=(200, 5000)
    ),
    
    "jiomart": MerchantEntry(
        name="JioMart",
        keywords=["jiomart", "jio mart", "reliance retail", "reliance fresh", "reliance smart"],
        category="Food & Dining",
        subcategory="Groceries",
        upi_patterns=["jiomart", "relianceretail"],
        typical_amount_range=(200, 5000)
    ),
    
    "dmart": MerchantEntry(
        name="DMart",
        keywords=["dmart", "d mart", "avenue supermarts", "dmart ready"],
        category="Food & Dining",
        subcategory="Groceries",
        upi_patterns=["dmart"],
        typical_amount_range=(500, 10000)
    ),
    
    "more_supermarket": MerchantEntry(
        name="More Supermarket",
        keywords=["more supermarket", "more megastore", "more retail"],
        category="Food & Dining",
        subcategory="Groceries",
        typical_amount_range=(200, 5000)
    ),
    
    "spencers": MerchantEntry(
        name="Spencer's",
        keywords=["spencers", "spencer's", "spencer retail"],
        category="Food & Dining",
        subcategory="Groceries",
        typical_amount_range=(200, 5000)
    ),
    
    "nature_basket": MerchantEntry(
        name="Nature's Basket",
        keywords=["natures basket", "nature's basket", "godrej nature's basket"],
        category="Food & Dining",
        subcategory="Groceries",
        typical_amount_range=(300, 5000)
    ),
    
    "milkbasket": MerchantEntry(
        name="Milkbasket",
        keywords=["milkbasket", "milk basket"],
        category="Food & Dining",
        subcategory="Groceries",
        typical_amount_range=(100, 1000)
    ),
    
    "country_delight": MerchantEntry(
        name="Country Delight",
        keywords=["country delight", "countrydelight"],
        category="Food & Dining",
        subcategory="Groceries",
        upi_patterns=["countrydelight"],
        typical_amount_range=(100, 1500)
    ),
    
    # ==========================================================================
    # E-COMMERCE PLATFORMS
    # ==========================================================================
    
    "amazon": MerchantEntry(
        name="Amazon",
        keywords=["amazon", "amzn", "amazon pay", "amazon prime", "amazon seller", "amazon fresh", "a]mazon"],
        category="Shopping",
        subcategory="Electronics",
        upi_patterns=["amazon", "amzn", "amazonpay"],
        confidence=0.85,
        typical_amount_range=(100, 50000)
    ),
    
    "flipkart": MerchantEntry(
        name="Flipkart",
        keywords=["flipkart", "flip kart", "flipkart internet", "ekart", "phonepe merchant"],
        category="Shopping",
        subcategory="Electronics",
        upi_patterns=["flipkart"],
        confidence=0.85,
        typical_amount_range=(100, 50000)
    ),
    
    "myntra": MerchantEntry(
        name="Myntra",
        keywords=["myntra", "myntra designs"],
        category="Shopping",
        subcategory="Clothes/Apparel",
        upi_patterns=["myntra"],
        typical_amount_range=(300, 10000)
    ),
    
    "ajio": MerchantEntry(
        name="AJIO",
        keywords=["ajio", "reliance ajio"],
        category="Shopping",
        subcategory="Clothes/Apparel",
        upi_patterns=["ajio"],
        typical_amount_range=(300, 8000)
    ),
    
    "meesho": MerchantEntry(
        name="Meesho",
        keywords=["meesho", "fashnear"],
        category="Shopping",
        subcategory="Clothes/Apparel",
        upi_patterns=["meesho"],
        typical_amount_range=(100, 3000)
    ),
    
    "snapdeal": MerchantEntry(
        name="Snapdeal",
        keywords=["snapdeal", "snap deal"],
        category="Shopping",
        subcategory="Electronics",
        upi_patterns=["snapdeal"],
        typical_amount_range=(100, 10000)
    ),
    
    "nykaa": MerchantEntry(
        name="Nykaa",
        keywords=["nykaa", "nykaa fashion", "nykaa e-retail"],
        category="Shopping",
        subcategory="Cosmetics",
        upi_patterns=["nykaa"],
        typical_amount_range=(200, 5000)
    ),
    
    "tata_cliq": MerchantEntry(
        name="Tata CLiQ",
        keywords=["tata cliq", "tatacliq", "cliq"],
        category="Shopping",
        subcategory="Electronics",
        upi_patterns=["tatacliq"],
        typical_amount_range=(500, 30000)
    ),
    
    "croma": MerchantEntry(
        name="Croma",
        keywords=["croma", "croma retail", "infiniti retail"],
        category="Shopping",
        subcategory="Electronics",
        upi_patterns=["croma"],
        typical_amount_range=(500, 100000)
    ),
    
    "vijay_sales": MerchantEntry(
        name="Vijay Sales",
        keywords=["vijay sales", "vijaysales"],
        category="Shopping",
        subcategory="Electronics",
        typical_amount_range=(500, 100000)
    ),
    
    "reliance_digital": MerchantEntry(
        name="Reliance Digital",
        keywords=["reliance digital", "reliancedigital", "digital xpress"],
        category="Shopping",
        subcategory="Electronics",
        upi_patterns=["reliancedigital"],
        typical_amount_range=(500, 100000)
    ),
    
    "pepperfry": MerchantEntry(
        name="Pepperfry",
        keywords=["pepperfry", "pepper fry"],
        category="Shopping",
        subcategory="Furniture",
        upi_patterns=["pepperfry"],
        typical_amount_range=(1000, 100000)
    ),
    
    "urban_ladder": MerchantEntry(
        name="Urban Ladder",
        keywords=["urban ladder", "urbanladder"],
        category="Shopping",
        subcategory="Furniture",
        typical_amount_range=(2000, 150000)
    ),
    
    "ikea": MerchantEntry(
        name="IKEA",
        keywords=["ikea", "ikea india"],
        category="Shopping",
        subcategory="Furniture",
        upi_patterns=["ikea"],
        typical_amount_range=(500, 100000)
    ),
    
    # ==========================================================================
    # RESTAURANTS & FOOD CHAINS
    # ==========================================================================
    
    "mcdonalds": MerchantEntry(
        name="McDonald's",
        keywords=["mcdonald", "mcdonalds", "mcd", "mcdelivery", "hardcastle"],
        category="Food & Dining",
        subcategory="Fast Food",
        upi_patterns=["mcdonalds"],
        typical_amount_range=(100, 1000)
    ),
    
    "kfc": MerchantEntry(
        name="KFC",
        keywords=["kfc", "kentucky fried", "kentucky", "devyani international"],
        category="Food & Dining",
        subcategory="Fast Food",
        upi_patterns=["kfc"],
        typical_amount_range=(150, 1000)
    ),
    
    "dominos": MerchantEntry(
        name="Domino's Pizza",
        keywords=["dominos", "domino's", "domino", "jubilant foodworks"],
        category="Food & Dining",
        subcategory="Fast Food",
        upi_patterns=["dominos"],
        typical_amount_range=(200, 1500)
    ),
    
    "pizza_hut": MerchantEntry(
        name="Pizza Hut",
        keywords=["pizza hut", "pizzahut"],
        category="Food & Dining",
        subcategory="Fast Food",
        upi_patterns=["pizzahut"],
        typical_amount_range=(300, 1500)
    ),
    
    "burger_king": MerchantEntry(
        name="Burger King",
        keywords=["burger king", "burgerking", "bk india"],
        category="Food & Dining",
        subcategory="Fast Food",
        upi_patterns=["burgerking"],
        typical_amount_range=(150, 800)
    ),
    
    "subway": MerchantEntry(
        name="Subway",
        keywords=["subway", "subway india"],
        category="Food & Dining",
        subcategory="Fast Food",
        upi_patterns=["subway"],
        typical_amount_range=(150, 600)
    ),
    
    "starbucks": MerchantEntry(
        name="Starbucks",
        keywords=["starbucks", "tata starbucks", "sbux"],
        category="Food & Dining",
        subcategory="Coffee/Tea",
        upi_patterns=["starbucks"],
        typical_amount_range=(200, 1000)
    ),
    
    "cafe_coffee_day": MerchantEntry(
        name="Cafe Coffee Day",
        keywords=["cafe coffee day", "ccd", "coffee day", "coffeeday"],
        category="Food & Dining",
        subcategory="Coffee/Tea",
        upi_patterns=["coffeeday", "ccd"],
        typical_amount_range=(100, 500)
    ),
    
    "barista": MerchantEntry(
        name="Barista",
        keywords=["barista", "barista coffee"],
        category="Food & Dining",
        subcategory="Coffee/Tea",
        typical_amount_range=(150, 600)
    ),
    
    "chaayos": MerchantEntry(
        name="Chaayos",
        keywords=["chaayos", "chai point", "chaipoint"],
        category="Food & Dining",
        subcategory="Coffee/Tea",
        upi_patterns=["chaayos", "chaipoint"],
        typical_amount_range=(50, 400)
    ),
    
    "haldirams": MerchantEntry(
        name="Haldiram's",
        keywords=["haldiram", "haldirams", "haldiram's"],
        category="Food & Dining",
        subcategory="Sweets/Mithai",
        upi_patterns=["haldirams"],
        typical_amount_range=(100, 2000)
    ),
    
    "bikanervala": MerchantEntry(
        name="Bikanervala",
        keywords=["bikanervala", "bikaner", "bikano"],
        category="Food & Dining",
        subcategory="Sweets/Mithai",
        typical_amount_range=(100, 2000)
    ),
    
    "baskin_robbins": MerchantEntry(
        name="Baskin Robbins",
        keywords=["baskin robbins", "baskinrobbins", "br ice cream"],
        category="Food & Dining",
        subcategory="Beverages",
        upi_patterns=["baskinrobbins"],
        typical_amount_range=(100, 500)
    ),
    
    "naturals": MerchantEntry(
        name="Naturals Ice Cream",
        keywords=["naturals", "naturals ice cream"],
        category="Food & Dining",
        subcategory="Beverages",
        typical_amount_range=(100, 500)
    ),
    
    "wow_momo": MerchantEntry(
        name="Wow! Momo",
        keywords=["wow momo", "wowmomo", "wow! momo"],
        category="Food & Dining",
        subcategory="Fast Food",
        upi_patterns=["wowmomo"],
        typical_amount_range=(100, 500)
    ),
    
    "faasos": MerchantEntry(
        name="Faasos",
        keywords=["faasos", "fassos", "rebel foods"],
        category="Food & Dining",
        subcategory="Fast Food",
        upi_patterns=["faasos"],
        typical_amount_range=(150, 600)
    ),
    
    "behrouz_biryani": MerchantEntry(
        name="Behrouz Biryani",
        keywords=["behrouz", "behrouz biryani"],
        category="Food & Dining",
        subcategory="Restaurants",
        typical_amount_range=(200, 800)
    ),
    
    "oven_story": MerchantEntry(
        name="Oven Story",
        keywords=["oven story", "ovenstory"],
        category="Food & Dining",
        subcategory="Fast Food",
        typical_amount_range=(300, 1000)
    ),
    
    # ==========================================================================
    # TELECOM & INTERNET SERVICES
    # ==========================================================================
    
    "jio": MerchantEntry(
        name="Reliance Jio",
        keywords=["jio", "reliance jio", "jio recharge", "jio fiber", "jio postpaid"],
        category="Utilities",
        subcategory="Mobile Recharge",
        upi_patterns=["jio", "reliancejio"],
        typical_amount_range=(100, 3000)
    ),
    
    "airtel": MerchantEntry(
        name="Airtel",
        keywords=["airtel", "bharti airtel", "airtel thanks", "airtel xstream", "airtel black", "airtel payments bank"],
        category="Utilities",
        subcategory="Mobile Recharge",
        upi_patterns=["airtel", "bhartiairtel"],
        typical_amount_range=(100, 3000)
    ),
    
    "vi": MerchantEntry(
        name="Vi (Vodafone Idea)",
        keywords=["vodafone", "idea", "vi", "vodafone idea", "vi recharge"],
        category="Utilities",
        subcategory="Mobile Recharge",
        upi_patterns=["vodafone", "vi", "idea"],
        typical_amount_range=(100, 2000)
    ),
    
    "bsnl": MerchantEntry(
        name="BSNL",
        keywords=["bsnl", "bharat sanchar", "bsnl broadband", "bsnl fiber"],
        category="Utilities",
        subcategory="Mobile Recharge",
        upi_patterns=["bsnl"],
        typical_amount_range=(100, 2000)
    ),
    
    "act_fibernet": MerchantEntry(
        name="ACT Fibernet",
        keywords=["act fibernet", "act broadband", "atria convergence"],
        category="Utilities",
        subcategory="Internet",
        upi_patterns=["actfibernet"],
        is_subscription=True,
        typical_amount_range=(500, 3000)
    ),
    
    "hathway": MerchantEntry(
        name="Hathway",
        keywords=["hathway", "hathway broadband", "hathway cable"],
        category="Utilities",
        subcategory="Internet",
        is_subscription=True,
        typical_amount_range=(500, 2000)
    ),
    
    "tata_sky": MerchantEntry(
        name="Tata Play (Sky)",
        keywords=["tata sky", "tata play", "tatasky", "tataplay"],
        category="Utilities",
        subcategory="DTH/Cable",
        upi_patterns=["tataplay", "tatasky"],
        is_subscription=True,
        typical_amount_range=(200, 1500)
    ),
    
    "dish_tv": MerchantEntry(
        name="Dish TV",
        keywords=["dish tv", "dishtv", "d2h", "videocon d2h"],
        category="Utilities",
        subcategory="DTH/Cable",
        upi_patterns=["dishtv", "d2h"],
        is_subscription=True,
        typical_amount_range=(200, 1000)
    ),
    
    "airtel_dth": MerchantEntry(
        name="Airtel DTH",
        keywords=["airtel dth", "airtel digital tv"],
        category="Utilities",
        subcategory="DTH/Cable",
        is_subscription=True,
        typical_amount_range=(200, 1000)
    ),
    
    "sun_direct": MerchantEntry(
        name="Sun Direct",
        keywords=["sun direct", "sundirect"],
        category="Utilities",
        subcategory="DTH/Cable",
        is_subscription=True,
        typical_amount_range=(150, 800)
    ),
    
    # ==========================================================================
    # ELECTRICITY BOARDS
    # ==========================================================================
    
    "tata_power": MerchantEntry(
        name="Tata Power",
        keywords=["tata power", "tatapower", "tpddl", "tata power delhi"],
        category="Utilities",
        subcategory="Electricity",
        upi_patterns=["tatapower", "tpddl"],
        typical_amount_range=(500, 10000)
    ),
    
    "bses": MerchantEntry(
        name="BSES",
        keywords=["bses", "bses rajdhani", "bses yamuna", "bypl", "brpl"],
        category="Utilities",
        subcategory="Electricity",
        upi_patterns=["bses", "bypl", "brpl"],
        typical_amount_range=(500, 10000)
    ),
    
    "adani_electricity": MerchantEntry(
        name="Adani Electricity",
        keywords=["adani electricity", "adani power", "aeml"],
        category="Utilities",
        subcategory="Electricity",
        upi_patterns=["adanielectricity"],
        typical_amount_range=(500, 15000)
    ),
    
    "best": MerchantEntry(
        name="BEST Electricity",
        keywords=["best electricity", "best undertaking", "brihanmumbai electric"],
        category="Utilities",
        subcategory="Electricity",
        typical_amount_range=(500, 10000)
    ),
    
    "msedcl": MerchantEntry(
        name="MSEDCL",
        keywords=["msedcl", "mahadiscom", "maharashtra electricity", "mseb"],
        category="Utilities",
        subcategory="Electricity",
        upi_patterns=["msedcl", "mahadiscom"],
        typical_amount_range=(300, 8000)
    ),
    
    "bescom": MerchantEntry(
        name="BESCOM",
        keywords=["bescom", "bangalore electricity", "karnataka electricity"],
        category="Utilities",
        subcategory="Electricity",
        upi_patterns=["bescom"],
        typical_amount_range=(300, 8000)
    ),
    
    "tangedco": MerchantEntry(
        name="TANGEDCO",
        keywords=["tangedco", "tneb", "tamil nadu electricity"],
        category="Utilities",
        subcategory="Electricity",
        upi_patterns=["tangedco", "tneb"],
        typical_amount_range=(300, 6000)
    ),
    
    "cesc": MerchantEntry(
        name="CESC",
        keywords=["cesc", "calcutta electric", "cesc kolkata"],
        category="Utilities",
        subcategory="Electricity",
        upi_patterns=["cesc"],
        typical_amount_range=(300, 8000)
    ),
    
    "uppcl": MerchantEntry(
        name="UPPCL",
        keywords=["uppcl", "up electricity", "uttar pradesh power"],
        category="Utilities",
        subcategory="Electricity",
        upi_patterns=["uppcl"],
        typical_amount_range=(300, 6000)
    ),
    
    "dgvcl": MerchantEntry(
        name="Gujarat Electricity",
        keywords=["dgvcl", "pgvcl", "mgvcl", "ugvcl", "torrent power", "gujarat electricity"],
        category="Utilities",
        subcategory="Electricity",
        upi_patterns=["dgvcl", "torrentpower"],
        typical_amount_range=(300, 8000)
    ),
    
    # ==========================================================================
    # GAS & WATER
    # ==========================================================================
    
    "indraprastha_gas": MerchantEntry(
        name="IGL",
        keywords=["igl", "indraprastha gas", "igl gas", "png bill"],
        category="Utilities",
        subcategory="Piped Gas",
        upi_patterns=["igl"],
        typical_amount_range=(500, 3000)
    ),
    
    "mahanagar_gas": MerchantEntry(
        name="Mahanagar Gas",
        keywords=["mahanagar gas", "mgl", "mumbai gas"],
        category="Utilities",
        subcategory="Piped Gas",
        upi_patterns=["mgl"],
        typical_amount_range=(500, 3000)
    ),
    
    "adani_gas": MerchantEntry(
        name="Adani Gas",
        keywords=["adani gas", "adani total gas"],
        category="Utilities",
        subcategory="Piped Gas",
        upi_patterns=["adanigas"],
        typical_amount_range=(500, 3000)
    ),
    
    "lpg_hp": MerchantEntry(
        name="HP Gas",
        keywords=["hp gas", "hp lpg", "hpcl lpg"],
        category="Utilities",
        subcategory="LPG Cylinder",
        upi_patterns=["hpgas"],
        typical_amount_range=(800, 1200)
    ),
    
    "lpg_indane": MerchantEntry(
        name="Indane Gas",
        keywords=["indane", "indane gas", "ioc lpg", "indian oil gas"],
        category="Utilities",
        subcategory="LPG Cylinder",
        upi_patterns=["indane"],
        typical_amount_range=(800, 1200)
    ),
    
    "lpg_bharat": MerchantEntry(
        name="Bharat Gas",
        keywords=["bharat gas", "bharatgas", "bpcl lpg"],
        category="Utilities",
        subcategory="LPG Cylinder",
        upi_patterns=["bharatgas"],
        typical_amount_range=(800, 1200)
    ),
    
    # ==========================================================================
    # OTT & ENTERTAINMENT SUBSCRIPTIONS
    # ==========================================================================
    
    "netflix": MerchantEntry(
        name="Netflix",
        keywords=["netflix", "netflix india", "netflix.com"],
        category="Entertainment",
        subcategory="OTT Subscriptions",
        upi_patterns=["netflix"],
        is_subscription=True,
        typical_amount_range=(149, 699)
    ),
    
    "prime_video": MerchantEntry(
        name="Amazon Prime",
        keywords=["prime video", "amazon prime", "prime membership"],
        category="Entertainment",
        subcategory="OTT Subscriptions",
        upi_patterns=["amazonprime"],
        is_subscription=True,
        typical_amount_range=(179, 1499)
    ),
    
    "disney_hotstar": MerchantEntry(
        name="Disney+ Hotstar",
        keywords=["hotstar", "disney hotstar", "disney+", "disney plus", "star india"],
        category="Entertainment",
        subcategory="OTT Subscriptions",
        upi_patterns=["hotstar", "disney"],
        is_subscription=True,
        typical_amount_range=(149, 1499)
    ),
    
    "spotify": MerchantEntry(
        name="Spotify",
        keywords=["spotify", "spotify india", "spotify premium"],
        category="Entertainment",
        subcategory="Music Subscriptions",
        upi_patterns=["spotify"],
        is_subscription=True,
        typical_amount_range=(59, 179)
    ),
    
    "youtube_premium": MerchantEntry(
        name="YouTube Premium",
        keywords=["youtube premium", "youtube music", "google youtube"],
        category="Entertainment",
        subcategory="OTT Subscriptions",
        upi_patterns=["youtube"],
        is_subscription=True,
        typical_amount_range=(129, 189)
    ),
    
    "sony_liv": MerchantEntry(
        name="SonyLIV",
        keywords=["sonyliv", "sony liv", "sony pictures"],
        category="Entertainment",
        subcategory="OTT Subscriptions",
        upi_patterns=["sonyliv"],
        is_subscription=True,
        typical_amount_range=(299, 999)
    ),
    
    "zee5": MerchantEntry(
        name="ZEE5",
        keywords=["zee5", "zee 5", "zee entertainment"],
        category="Entertainment",
        subcategory="OTT Subscriptions",
        upi_patterns=["zee5"],
        is_subscription=True,
        typical_amount_range=(99, 999)
    ),
    
    "jio_cinema": MerchantEntry(
        name="JioCinema",
        keywords=["jiocinema", "jio cinema"],
        category="Entertainment",
        subcategory="OTT Subscriptions",
        upi_patterns=["jiocinema"],
        is_subscription=True,
        typical_amount_range=(29, 999)
    ),
    
    "apple_music": MerchantEntry(
        name="Apple Music",
        keywords=["apple music", "apple one", "apple subscription"],
        category="Entertainment",
        subcategory="Music Subscriptions",
        upi_patterns=["apple"],
        is_subscription=True,
        typical_amount_range=(99, 199)
    ),
    
    "gaana": MerchantEntry(
        name="Gaana",
        keywords=["gaana", "gaana plus", "gaana premium"],
        category="Entertainment",
        subcategory="Music Subscriptions",
        upi_patterns=["gaana"],
        is_subscription=True,
        typical_amount_range=(99, 399)
    ),
    
    "bookmyshow": MerchantEntry(
        name="BookMyShow",
        keywords=["bookmyshow", "book my show", "bms", "bigtree entertainment"],
        category="Entertainment",
        subcategory="Movies/Cinema",
        upi_patterns=["bookmyshow", "bms"],
        typical_amount_range=(150, 2000)
    ),
    
    "paytm_insider": MerchantEntry(
        name="Paytm Insider",
        keywords=["paytm insider", "insider.in"],
        category="Entertainment",
        subcategory="Events/Concerts",
        upi_patterns=["insider"],
        typical_amount_range=(300, 10000)
    ),
    
    # ==========================================================================
    # HEALTHCARE & PHARMACY
    # ==========================================================================
    
    "apollo_pharmacy": MerchantEntry(
        name="Apollo Pharmacy",
        keywords=["apollo pharmacy", "apollo 24x7", "apollo hospitals", "apollo health"],
        category="Healthcare",
        subcategory="Medicines",
        upi_patterns=["apollo", "apollopharmacy"],
        typical_amount_range=(100, 5000)
    ),
    
    "pharmeasy": MerchantEntry(
        name="PharmEasy",
        keywords=["pharmeasy", "pharm easy", "api holdings"],
        category="Healthcare",
        subcategory="Medicines",
        upi_patterns=["pharmeasy"],
        typical_amount_range=(100, 3000)
    ),
    
    "onemg": MerchantEntry(
        name="1mg",
        keywords=["1mg", "one mg", "tata 1mg"],
        category="Healthcare",
        subcategory="Medicines",
        upi_patterns=["1mg", "onemg"],
        typical_amount_range=(100, 3000)
    ),
    
    "netmeds": MerchantEntry(
        name="Netmeds",
        keywords=["netmeds", "net meds", "reliance netmeds"],
        category="Healthcare",
        subcategory="Medicines",
        upi_patterns=["netmeds"],
        typical_amount_range=(100, 3000)
    ),
    
    "medplus": MerchantEntry(
        name="MedPlus",
        keywords=["medplus", "med plus"],
        category="Healthcare",
        subcategory="Medicines",
        typical_amount_range=(100, 2000)
    ),
    
    "practo": MerchantEntry(
        name="Practo",
        keywords=["practo", "practo consult"],
        category="Healthcare",
        subcategory="Doctor/Hospital",
        upi_patterns=["practo"],
        typical_amount_range=(200, 1500)
    ),
    
    "thyrocare": MerchantEntry(
        name="Thyrocare",
        keywords=["thyrocare", "thyrocare labs"],
        category="Healthcare",
        subcategory="Lab Tests",
        upi_patterns=["thyrocare"],
        typical_amount_range=(300, 5000)
    ),
    
    "dr_lal_path": MerchantEntry(
        name="Dr Lal PathLabs",
        keywords=["dr lal", "lal path labs", "lal pathlabs"],
        category="Healthcare",
        subcategory="Lab Tests",
        upi_patterns=["lalpathlabs"],
        typical_amount_range=(200, 10000)
    ),
    
    "srl_diagnostics": MerchantEntry(
        name="SRL Diagnostics",
        keywords=["srl", "srl diagnostics"],
        category="Healthcare",
        subcategory="Lab Tests",
        typical_amount_range=(200, 8000)
    ),
    
    "cultfit": MerchantEntry(
        name="Cult.fit",
        keywords=["cult.fit", "cultfit", "cure.fit", "curefit"],
        category="Healthcare",
        subcategory="Gym/Fitness",
        upi_patterns=["cultfit", "curefit"],
        is_subscription=True,
        typical_amount_range=(500, 5000)
    ),
    
    "gold_gym": MerchantEntry(
        name="Gold's Gym",
        keywords=["golds gym", "gold's gym", "gold gym"],
        category="Healthcare",
        subcategory="Gym/Fitness",
        is_subscription=True,
        typical_amount_range=(1000, 5000)
    ),
    
    # ==========================================================================
    # TRAVEL & BOOKING
    # ==========================================================================
    
    "makemytrip": MerchantEntry(
        name="MakeMyTrip",
        keywords=["makemytrip", "make my trip", "mmt", "goibibo"],
        category="Travel",
        subcategory="Flight",
        upi_patterns=["makemytrip", "mmt"],
        typical_amount_range=(500, 50000)
    ),
    
    "goibibo": MerchantEntry(
        name="Goibibo",
        keywords=["goibibo", "go ibibo"],
        category="Travel",
        subcategory="Flight",
        upi_patterns=["goibibo"],
        typical_amount_range=(500, 40000)
    ),
    
    "cleartrip": MerchantEntry(
        name="Cleartrip",
        keywords=["cleartrip", "clear trip"],
        category="Travel",
        subcategory="Flight",
        upi_patterns=["cleartrip"],
        typical_amount_range=(500, 50000)
    ),
    
    "yatra": MerchantEntry(
        name="Yatra",
        keywords=["yatra", "yatra.com"],
        category="Travel",
        subcategory="Flight",
        upi_patterns=["yatra"],
        typical_amount_range=(500, 40000)
    ),
    
    "ixigo": MerchantEntry(
        name="Ixigo",
        keywords=["ixigo", "le travenues"],
        category="Travel",
        subcategory="Train",
        upi_patterns=["ixigo"],
        typical_amount_range=(100, 5000)
    ),
    
    "redbus": MerchantEntry(
        name="RedBus",
        keywords=["redbus", "red bus", "ibibo redbus"],
        category="Travel",
        subcategory="Bus",
        upi_patterns=["redbus"],
        typical_amount_range=(200, 3000)
    ),
    
    "oyo": MerchantEntry(
        name="OYO",
        keywords=["oyo", "oyo rooms", "oravel stays"],
        category="Travel",
        subcategory="Hotel",
        upi_patterns=["oyo", "oyorooms"],
        typical_amount_range=(500, 10000)
    ),
    
    "treebo": MerchantEntry(
        name="Treebo",
        keywords=["treebo", "treebo hotels"],
        category="Travel",
        subcategory="Hotel",
        upi_patterns=["treebo"],
        typical_amount_range=(800, 8000)
    ),
    
    "fab_hotels": MerchantEntry(
        name="FabHotels",
        keywords=["fabhotels", "fab hotels"],
        category="Travel",
        subcategory="Hotel",
        upi_patterns=["fabhotels"],
        typical_amount_range=(700, 6000)
    ),
    
    "airbnb": MerchantEntry(
        name="Airbnb",
        keywords=["airbnb", "air bnb"],
        category="Travel",
        subcategory="Homestay",
        upi_patterns=["airbnb"],
        typical_amount_range=(1000, 20000)
    ),
    
    "zostel": MerchantEntry(
        name="Zostel",
        keywords=["zostel", "zo rooms"],
        category="Travel",
        subcategory="Hotel",
        typical_amount_range=(500, 3000)
    ),
    
    "indigo": MerchantEntry(
        name="IndiGo Airlines",
        keywords=["indigo", "interglobe", "6e airlines"],
        category="Travel",
        subcategory="Flight",
        upi_patterns=["indigo"],
        typical_amount_range=(2000, 30000)
    ),
    
    "air_india": MerchantEntry(
        name="Air India",
        keywords=["air india", "airindia", "air india express"],
        category="Travel",
        subcategory="Flight",
        upi_patterns=["airindia"],
        typical_amount_range=(2500, 50000)
    ),
    
    "vistara": MerchantEntry(
        name="Vistara",
        keywords=["vistara", "tata sia"],
        category="Travel",
        subcategory="Flight",
        upi_patterns=["vistara"],
        typical_amount_range=(3000, 40000)
    ),
    
    "spicejet": MerchantEntry(
        name="SpiceJet",
        keywords=["spicejet", "spice jet"],
        category="Travel",
        subcategory="Flight",
        upi_patterns=["spicejet"],
        typical_amount_range=(2000, 25000)
    ),
    
    # ==========================================================================
    # EDUCATION & LEARNING
    # ==========================================================================
    
    "byjus": MerchantEntry(
        name="BYJU'S",
        keywords=["byjus", "byju's", "think and learn"],
        category="Education",
        subcategory="Online Courses",
        upi_patterns=["byjus"],
        is_subscription=True,
        typical_amount_range=(500, 50000)
    ),
    
    "unacademy": MerchantEntry(
        name="Unacademy",
        keywords=["unacademy", "unacademy plus"],
        category="Education",
        subcategory="Online Courses",
        upi_patterns=["unacademy"],
        is_subscription=True,
        typical_amount_range=(500, 30000)
    ),
    
    "vedantu": MerchantEntry(
        name="Vedantu",
        keywords=["vedantu"],
        category="Education",
        subcategory="Online Courses",
        upi_patterns=["vedantu"],
        is_subscription=True,
        typical_amount_range=(500, 25000)
    ),
    
    "physics_wallah": MerchantEntry(
        name="Physics Wallah",
        keywords=["physics wallah", "pw", "alakh pandey"],
        category="Education",
        subcategory="Coaching",
        upi_patterns=["physicswallah"],
        typical_amount_range=(500, 15000)
    ),
    
    "coursera": MerchantEntry(
        name="Coursera",
        keywords=["coursera"],
        category="Education",
        subcategory="Online Courses",
        upi_patterns=["coursera"],
        is_subscription=True,
        typical_amount_range=(1500, 5000)
    ),
    
    "udemy": MerchantEntry(
        name="Udemy",
        keywords=["udemy"],
        category="Education",
        subcategory="Online Courses",
        upi_patterns=["udemy"],
        typical_amount_range=(400, 3000)
    ),
    
    "skillshare": MerchantEntry(
        name="Skillshare",
        keywords=["skillshare"],
        category="Education",
        subcategory="Skill Development",
        upi_patterns=["skillshare"],
        is_subscription=True,
        typical_amount_range=(500, 2500)
    ),
    
    "linkedin_learning": MerchantEntry(
        name="LinkedIn Learning",
        keywords=["linkedin learning", "linkedin premium"],
        category="Education",
        subcategory="Skill Development",
        upi_patterns=["linkedin"],
        is_subscription=True,
        typical_amount_range=(500, 2000)
    ),
    
    "upgrad": MerchantEntry(
        name="upGrad",
        keywords=["upgrad", "up grad"],
        category="Education",
        subcategory="Certifications",
        upi_patterns=["upgrad"],
        typical_amount_range=(10000, 300000)
    ),
    
    "simplilearn": MerchantEntry(
        name="Simplilearn",
        keywords=["simplilearn"],
        category="Education",
        subcategory="Certifications",
        upi_patterns=["simplilearn"],
        typical_amount_range=(5000, 150000)
    ),
    
    # ==========================================================================
    # PAYMENT APPS & WALLETS
    # ==========================================================================
    
    "paytm": MerchantEntry(
        name="Paytm",
        keywords=["paytm", "paytm wallet", "paytm payments", "one97"],
        category="Transfer",
        subcategory="Wallet Load",
        upi_patterns=["paytm"],
        confidence=0.70,
        typical_amount_range=(100, 10000)
    ),
    
    "phonepe": MerchantEntry(
        name="PhonePe",
        keywords=["phonepe", "phone pe"],
        category="Transfer",
        subcategory="UPI Transfer",
        upi_patterns=["phonepe"],
        confidence=0.70,
        typical_amount_range=(100, 100000)
    ),
    
    "gpay": MerchantEntry(
        name="Google Pay",
        keywords=["google pay", "gpay", "tez"],
        category="Transfer",
        subcategory="UPI Transfer",
        upi_patterns=["googlepay", "gpay", "tez"],
        confidence=0.70,
        typical_amount_range=(100, 100000)
    ),
    
    "amazon_pay": MerchantEntry(
        name="Amazon Pay",
        keywords=["amazon pay", "amazpay"],
        category="Transfer",
        subcategory="Wallet Load",
        upi_patterns=["amazonpay", "amazpay"],
        confidence=0.70,
        typical_amount_range=(100, 10000)
    ),
    
    "mobikwik": MerchantEntry(
        name="MobiKwik",
        keywords=["mobikwik", "mobi kwik"],
        category="Transfer",
        subcategory="Wallet Load",
        upi_patterns=["mobikwik"],
        typical_amount_range=(100, 10000)
    ),
    
    "freecharge": MerchantEntry(
        name="Freecharge",
        keywords=["freecharge", "free charge"],
        category="Transfer",
        subcategory="Wallet Load",
        upi_patterns=["freecharge"],
        typical_amount_range=(100, 10000)
    ),
    
    # ==========================================================================
    # BANKS - For transfers and payments
    # ==========================================================================
    
    "hdfc_bank": MerchantEntry(
        name="HDFC Bank",
        keywords=["hdfc", "hdfc bank", "hdfc ltd"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["hdfc", "hdfcbank"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "sbi": MerchantEntry(
        name="State Bank of India",
        keywords=["sbi", "state bank", "state bank of india"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["sbi", "statebank"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "icici_bank": MerchantEntry(
        name="ICICI Bank",
        keywords=["icici", "icici bank"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["icici", "icicibank"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "axis_bank": MerchantEntry(
        name="Axis Bank",
        keywords=["axis", "axis bank", "uti bank"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["axis", "axisbank"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "kotak_bank": MerchantEntry(
        name="Kotak Mahindra Bank",
        keywords=["kotak", "kotak mahindra", "kotak bank"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["kotak", "kotakbank"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "yes_bank": MerchantEntry(
        name="Yes Bank",
        keywords=["yes bank", "yesbank"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["yesbank"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "idfc_bank": MerchantEntry(
        name="IDFC First Bank",
        keywords=["idfc", "idfc first", "idfc bank"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["idfc", "idfcfirst"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "indusind_bank": MerchantEntry(
        name="IndusInd Bank",
        keywords=["indusind", "indusind bank"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["indusind"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "pnb": MerchantEntry(
        name="Punjab National Bank",
        keywords=["pnb", "punjab national", "punjab national bank"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["pnb"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "bob": MerchantEntry(
        name="Bank of Baroda",
        keywords=["bob", "bank of baroda", "baroda bank"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["bankofbaroda", "bob"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "canara_bank": MerchantEntry(
        name="Canara Bank",
        keywords=["canara", "canara bank"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["canarabank"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    "union_bank": MerchantEntry(
        name="Union Bank",
        keywords=["union bank", "union bank of india"],
        category="Financial",
        subcategory="Bank Charges",
        upi_patterns=["unionbank"],
        confidence=0.60,
        typical_amount_range=(0, 1000000)
    ),
    
    # ==========================================================================
    # INSURANCE
    # ==========================================================================
    
    "lic": MerchantEntry(
        name="LIC",
        keywords=["lic", "life insurance corporation", "lic india", "lic premium"],
        category="Financial",
        subcategory="Insurance Premium",
        upi_patterns=["lic", "licindia"],
        is_subscription=True,
        typical_amount_range=(500, 100000)
    ),
    
    "hdfc_life": MerchantEntry(
        name="HDFC Life",
        keywords=["hdfc life", "hdfclife", "hdfc standard life"],
        category="Financial",
        subcategory="Insurance Premium",
        upi_patterns=["hdfclife"],
        is_subscription=True,
        typical_amount_range=(1000, 50000)
    ),
    
    "icici_prudential": MerchantEntry(
        name="ICICI Prudential",
        keywords=["icici prudential", "icici pru", "iprulife"],
        category="Financial",
        subcategory="Insurance Premium",
        upi_patterns=["icicipru"],
        is_subscription=True,
        typical_amount_range=(1000, 50000)
    ),
    
    "sbi_life": MerchantEntry(
        name="SBI Life",
        keywords=["sbi life", "sbilife"],
        category="Financial",
        subcategory="Insurance Premium",
        upi_patterns=["sbilife"],
        is_subscription=True,
        typical_amount_range=(1000, 50000)
    ),
    
    "max_life": MerchantEntry(
        name="Max Life",
        keywords=["max life", "maxlife", "max bupa"],
        category="Financial",
        subcategory="Insurance Premium",
        upi_patterns=["maxlife"],
        is_subscription=True,
        typical_amount_range=(1000, 50000)
    ),
    
    "star_health": MerchantEntry(
        name="Star Health",
        keywords=["star health", "starhealth", "star health insurance"],
        category="Healthcare",
        subcategory="Health Insurance",
        upi_patterns=["starhealth"],
        is_subscription=True,
        typical_amount_range=(5000, 50000)
    ),
    
    "care_health": MerchantEntry(
        name="Care Health",
        keywords=["care health", "religare health", "care insurance"],
        category="Healthcare",
        subcategory="Health Insurance",
        is_subscription=True,
        typical_amount_range=(5000, 50000)
    ),
    
    "icici_lombard": MerchantEntry(
        name="ICICI Lombard",
        keywords=["icici lombard", "icicilombard"],
        category="Financial",
        subcategory="Insurance Premium",
        upi_patterns=["icicilombard"],
        is_subscription=True,
        typical_amount_range=(1000, 30000)
    ),
    
    "bajaj_allianz": MerchantEntry(
        name="Bajaj Allianz",
        keywords=["bajaj allianz", "bajajallianz"],
        category="Financial",
        subcategory="Insurance Premium",
        upi_patterns=["bajajallianz"],
        is_subscription=True,
        typical_amount_range=(1000, 30000)
    ),
    
    # ==========================================================================
    # INVESTMENTS & MUTUAL FUNDS
    # ==========================================================================
    
    "zerodha": MerchantEntry(
        name="Zerodha",
        keywords=["zerodha", "zerodha broking", "coin by zerodha"],
        category="Financial",
        subcategory="Stock Purchase",
        upi_patterns=["zerodha"],
        typical_amount_range=(500, 500000)
    ),
    
    "groww": MerchantEntry(
        name="Groww",
        keywords=["groww", "groww invest"],
        category="Financial",
        subcategory="Investment",
        upi_patterns=["groww"],
        typical_amount_range=(100, 100000)
    ),
    
    "upstox": MerchantEntry(
        name="Upstox",
        keywords=["upstox", "rksv"],
        category="Financial",
        subcategory="Stock Purchase",
        upi_patterns=["upstox"],
        typical_amount_range=(500, 200000)
    ),
    
    "kuvera": MerchantEntry(
        name="Kuvera",
        keywords=["kuvera"],
        category="Financial",
        subcategory="Mutual Fund",
        upi_patterns=["kuvera"],
        typical_amount_range=(500, 100000)
    ),
    
    "paytm_money": MerchantEntry(
        name="Paytm Money",
        keywords=["paytm money", "paytmmoney"],
        category="Financial",
        subcategory="Investment",
        upi_patterns=["paytmmoney"],
        typical_amount_range=(100, 100000)
    ),
    
    "etmoney": MerchantEntry(
        name="ET Money",
        keywords=["etmoney", "et money", "times internet"],
        category="Financial",
        subcategory="Mutual Fund",
        upi_patterns=["etmoney"],
        typical_amount_range=(500, 100000)
    ),
    
    "sip_cams": MerchantEntry(
        name="CAMS (MF)",
        keywords=["cams", "computer age management", "camsonline"],
        category="Financial",
        subcategory="SIP",
        upi_patterns=["cams"],
        is_subscription=True,
        typical_amount_range=(500, 100000)
    ),
    
    "sip_kfintech": MerchantEntry(
        name="KFintech (MF)",
        keywords=["kfintech", "karvy", "kfin"],
        category="Financial",
        subcategory="SIP",
        upi_patterns=["kfintech"],
        is_subscription=True,
        typical_amount_range=(500, 100000)
    ),
    
    # ==========================================================================
    # PERSONAL CARE & LIFESTYLE
    # ==========================================================================
    
    "urban_company": MerchantEntry(
        name="Urban Company",
        keywords=["urban company", "urbancompany", "urban clap", "urbanclap"],
        category="Personal",
        subcategory="Personal Care",
        upi_patterns=["urbancompany", "urbanclap"],
        typical_amount_range=(200, 5000)
    ),
    
    "lakme": MerchantEntry(
        name="Lakme Salon",
        keywords=["lakme", "lakme salon", "lakme lever"],
        category="Personal",
        subcategory="Salon/Spa",
        typical_amount_range=(500, 5000)
    ),
    
    "jawed_habib": MerchantEntry(
        name="Jawed Habib",
        keywords=["jawed habib", "jawedhabib"],
        category="Personal",
        subcategory="Salon/Spa",
        typical_amount_range=(200, 2000)
    ),
    
    "vlcc": MerchantEntry(
        name="VLCC",
        keywords=["vlcc", "vlcc wellness"],
        category="Personal",
        subcategory="Salon/Spa",
        typical_amount_range=(500, 10000)
    ),
    
    "dry_cleaners": MerchantEntry(
        name="Laundry Service",
        keywords=["laundry", "dry clean", "dryclean", "washmart", "uclean", "laundromat", "pressto"],
        category="Personal",
        subcategory="Laundry",
        typical_amount_range=(100, 1000)
    ),
    
    # ==========================================================================
    # CREDIT CARDS & LOANS
    # ==========================================================================
    
    "hdfc_cc": MerchantEntry(
        name="HDFC Credit Card",
        keywords=["hdfc credit card", "hdfc card", "hdfccc", "hdfc cc payment"],
        category="Financial",
        subcategory="Credit Card Bill",
        upi_patterns=["hdfccc", "hdfccreditcard"],
        typical_amount_range=(1000, 500000)
    ),
    
    "icici_cc": MerchantEntry(
        name="ICICI Credit Card",
        keywords=["icici credit card", "icici card", "icicicc"],
        category="Financial",
        subcategory="Credit Card Bill",
        upi_patterns=["icicicc"],
        typical_amount_range=(1000, 500000)
    ),
    
    "sbi_cc": MerchantEntry(
        name="SBI Credit Card",
        keywords=["sbi card", "sbi credit card", "sbicard"],
        category="Financial",
        subcategory="Credit Card Bill",
        upi_patterns=["sbicard"],
        typical_amount_range=(1000, 500000)
    ),
    
    "axis_cc": MerchantEntry(
        name="Axis Credit Card",
        keywords=["axis credit card", "axis card"],
        category="Financial",
        subcategory="Credit Card Bill",
        upi_patterns=["axiscc", "axiscard"],
        typical_amount_range=(1000, 500000)
    ),
    
    "amex": MerchantEntry(
        name="American Express",
        keywords=["amex", "american express", "americanexpress"],
        category="Financial",
        subcategory="Credit Card Bill",
        upi_patterns=["amex"],
        typical_amount_range=(1000, 500000)
    ),
    
    "bajaj_finserv": MerchantEntry(
        name="Bajaj Finserv",
        keywords=["bajaj finserv", "bajaj finance", "bajaj emi"],
        category="Financial",
        subcategory="EMI Payment",
        upi_patterns=["bajajfinserv"],
        is_subscription=True,
        typical_amount_range=(1000, 50000)
    ),
    
    "home_credit": MerchantEntry(
        name="Home Credit",
        keywords=["home credit", "homecredit"],
        category="Financial",
        subcategory="EMI Payment",
        upi_patterns=["homecredit"],
        is_subscription=True,
        typical_amount_range=(1000, 30000)
    ),
    
    "tata_capital": MerchantEntry(
        name="Tata Capital",
        keywords=["tata capital", "tatacapital"],
        category="Financial",
        subcategory="EMI Payment",
        upi_patterns=["tatacapital"],
        is_subscription=True,
        typical_amount_range=(2000, 100000)
    ),
    
    # ==========================================================================
    # GOVERNMENT & TAX
    # ==========================================================================
    
    "income_tax": MerchantEntry(
        name="Income Tax",
        keywords=["income tax", "it dept", "tds", "advance tax", "self assessment tax"],
        category="Financial",
        subcategory="Tax Payment",
        upi_patterns=["incometax"],
        typical_amount_range=(1000, 500000)
    ),
    
    "gst_payment": MerchantEntry(
        name="GST",
        keywords=["gst", "gst payment", "goods and service tax"],
        category="Financial",
        subcategory="GST",
        typical_amount_range=(1000, 100000)
    ),
    
    "mcd_tax": MerchantEntry(
        name="Municipal Tax",
        keywords=["mcd", "municipal", "property tax", "house tax", "corporation tax"],
        category="Housing",
        subcategory="Property Tax",
        typical_amount_range=(1000, 50000)
    ),
    
    "rti_fee": MerchantEntry(
        name="Government Fees",
        keywords=["rti", "passport fee", "visa fee", "stamp duty", "registration fee"],
        category="Personal",
        subcategory="Miscellaneous",
        typical_amount_range=(10, 100000)
    ),
}


class MerchantDictionary:
    """
    A comprehensive dictionary for Indian merchant lookup and categorization.
    
    Provides methods for:
    - Exact keyword matching
    - Fuzzy matching with Levenshtein distance
    - UPI pattern matching
    - Category inference from partial matches
    """
    
    def __init__(self):
        """Initialize the merchant dictionary with indexes for fast lookup."""
        self.merchants = MERCHANT_CATEGORIES
        self._build_indexes()
    
    def _build_indexes(self):
        """Build reverse indexes for fast lookup."""
        # Keyword to merchant mapping
        self.keyword_index: Dict[str, List[str]] = {}
        # UPI pattern to merchant mapping
        self.upi_index: Dict[str, str] = {}
        # Category to merchants mapping
        self.category_index: Dict[str, List[str]] = {}
        # Subcategory to merchants mapping
        self.subcategory_index: Dict[str, List[str]] = {}
        # Subscription merchants
        self.subscription_merchants: Set[str] = set()
        
        for merchant_id, entry in self.merchants.items():
            # Index keywords
            for keyword in entry.keywords:
                keyword_lower = keyword.lower()
                if keyword_lower not in self.keyword_index:
                    self.keyword_index[keyword_lower] = []
                self.keyword_index[keyword_lower].append(merchant_id)
            
            # Index UPI patterns
            for pattern in entry.upi_patterns:
                self.upi_index[pattern.lower()] = merchant_id
            
            # Index by category
            if entry.category not in self.category_index:
                self.category_index[entry.category] = []
            self.category_index[entry.category].append(merchant_id)
            
            # Index by subcategory
            if entry.subcategory not in self.subcategory_index:
                self.subcategory_index[entry.subcategory] = []
            self.subcategory_index[entry.subcategory].append(merchant_id)
            
            # Track subscription merchants
            if entry.is_subscription:
                self.subscription_merchants.add(merchant_id)
    
    def lookup_exact(self, text: str) -> Optional[MerchantEntry]:
        """
        Perform exact keyword lookup.
        
        Args:
            text: The text to search for merchants
            
        Returns:
            MerchantEntry if exact match found, None otherwise
        """
        text_lower = text.lower().strip()
        
        # Direct keyword match
        if text_lower in self.keyword_index:
            merchant_id = self.keyword_index[text_lower][0]
            return self.merchants[merchant_id]
        
        return None
    
    def lookup_contains(self, text: str) -> List[Tuple[MerchantEntry, float]]:
        """
        Find all merchants whose keywords are contained in the text.
        
        Args:
            text: The transaction description to search
            
        Returns:
            List of (MerchantEntry, confidence) tuples, sorted by confidence
        """
        text_lower = text.lower()
        matches: List[Tuple[MerchantEntry, float]] = []
        seen_merchants: Set[str] = set()
        
        for keyword, merchant_ids in self.keyword_index.items():
            if keyword in text_lower:
                for merchant_id in merchant_ids:
                    if merchant_id not in seen_merchants:
                        entry = self.merchants[merchant_id]
                        # Confidence based on keyword length and match quality
                        keyword_ratio = len(keyword) / len(text_lower)
                        confidence = min(0.95, entry.confidence * (0.5 + 0.5 * keyword_ratio))
                        matches.append((entry, confidence))
                        seen_merchants.add(merchant_id)
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def lookup_upi(self, upi_id: str) -> Optional[MerchantEntry]:
        """
        Lookup merchant by UPI ID pattern.
        
        Args:
            upi_id: The UPI ID to match (e.g., 'swiggy@upi')
            
        Returns:
            MerchantEntry if pattern matched, None otherwise
        """
        upi_lower = upi_id.lower()
        
        # Extract the handle part (before @)
        handle = upi_lower.split('@')[0] if '@' in upi_lower else upi_lower
        
        # Check against UPI patterns
        for pattern, merchant_id in self.upi_index.items():
            if pattern in handle:
                return self.merchants[merchant_id]
        
        return None
    
    def lookup_fuzzy(
        self,
        text: str,
        threshold: float = 0.7,
        max_results: int = 5
    ) -> List[Tuple[MerchantEntry, float]]:
        """
        Perform fuzzy matching using Levenshtein distance.
        
        Args:
            text: The text to match against
            threshold: Minimum similarity score (0.0 to 1.0)
            max_results: Maximum number of results to return
            
        Returns:
            List of (MerchantEntry, similarity) tuples
        """
        text_lower = text.lower().strip()
        results: List[Tuple[MerchantEntry, float]] = []
        seen_merchants: Set[str] = set()
        
        for keyword, merchant_ids in self.keyword_index.items():
            similarity = self._string_similarity(text_lower, keyword)
            if similarity >= threshold:
                for merchant_id in merchant_ids:
                    if merchant_id not in seen_merchants:
                        entry = self.merchants[merchant_id]
                        results.append((entry, similarity * entry.confidence))
                        seen_merchants.add(merchant_id)
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein ratio.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        # Calculate Levenshtein distance
        len1, len2 = len(s1), len(s2)
        
        # Early exit for very different lengths
        if abs(len1 - len2) > max(len1, len2) * 0.5:
            return 0.0
        
        # Create distance matrix
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,      # deletion
                    matrix[i][j - 1] + 1,      # insertion
                    matrix[i - 1][j - 1] + cost  # substitution
                )
        
        distance = matrix[len1][len2]
        max_len = max(len1, len2)
        return 1.0 - (distance / max_len)
    
    def get_merchants_by_category(self, category: str) -> List[MerchantEntry]:
        """Get all merchants in a specific category."""
        merchant_ids = self.category_index.get(category, [])
        return [self.merchants[mid] for mid in merchant_ids]
    
    def get_merchants_by_subcategory(self, subcategory: str) -> List[MerchantEntry]:
        """Get all merchants in a specific subcategory."""
        merchant_ids = self.subcategory_index.get(subcategory, [])
        return [self.merchants[mid] for mid in merchant_ids]
    
    def get_subscription_merchants(self) -> List[MerchantEntry]:
        """Get all merchants that are typically subscriptions."""
        return [self.merchants[mid] for mid in self.subscription_merchants]
    
    def is_subscription_merchant(self, merchant_name: str) -> bool:
        """Check if a merchant is a subscription-based service."""
        result = self.lookup_contains(merchant_name)
        if result:
            entry, _ = result[0]
            return entry.is_subscription
        return False
    
    def get_amount_category_hints(self, amount: float) -> List[str]:
        """
        Get category hints based on transaction amount.
        
        Args:
            amount: Transaction amount in INR
            
        Returns:
            List of likely categories for this amount range
        """
        hints: List[str] = []
        
        for merchant_id, entry in self.merchants.items():
            if entry.typical_amount_range:
                min_amt, max_amt = entry.typical_amount_range
                if min_amt <= amount <= max_amt:
                    if entry.category not in hints:
                        hints.append(entry.category)
        
        return hints
    
    def get_all_keywords(self) -> List[str]:
        """Get all keywords in the dictionary."""
        return list(self.keyword_index.keys())
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the merchant dictionary."""
        return {
            "total_merchants": len(self.merchants),
            "total_keywords": len(self.keyword_index),
            "total_upi_patterns": len(self.upi_index),
            "total_categories": len(self.category_index),
            "total_subcategories": len(self.subcategory_index),
            "subscription_merchants": len(self.subscription_merchants),
        }


# Common bank transaction patterns
BANK_PATTERNS = {
    "salary": {
        "patterns": [
            r"salary",
            r"sal\s*cr",
            r"payroll",
            r"stipend",
            r"wages",
            r"emoluments",
        ],
        "category": "Income",
        "subcategory": "Salary"
    },
    "atm_withdrawal": {
        "patterns": [
            r"atm\s*(wd|wdl|withdrawal|cash)",
            r"cash\s*wd",
            r"nfs.*wd",
            r"atm.*withdrawal",
        ],
        "category": "Transfer",
        "subcategory": "Self Transfer"
    },
    "neft_rtgs": {
        "patterns": [
            r"neft",
            r"rtgs",
            r"imps",
            r"ft\s*cr",
            r"ft\s*dr",
            r"fund\s*transfer",
        ],
        "category": "Transfer",
        "subcategory": "NEFT/RTGS/IMPS"
    },
    "upi": {
        "patterns": [
            r"upi[/-]",
            r"upi\s*cr",
            r"upi\s*dr",
            r"@\w+",
        ],
        "category": "Transfer",
        "subcategory": "UPI Transfer"
    },
    "emi": {
        "patterns": [
            r"emi",
            r"loan\s*emi",
            r"auto\s*debit.*emi",
            r"si.*emi",
        ],
        "category": "Financial",
        "subcategory": "EMI Payment"
    },
    "interest": {
        "patterns": [
            r"int\s*(cr|paid)",
            r"interest\s*(credit|earned)",
            r"savings\s*interest",
        ],
        "category": "Income",
        "subcategory": "Interest Income"
    },
    "dividend": {
        "patterns": [
            r"dividend",
            r"div\s*cr",
        ],
        "category": "Income",
        "subcategory": "Dividend"
    },
    "cashback": {
        "patterns": [
            r"cashback",
            r"cash\s*back",
            r"cb\s*cr",
            r"reward",
        ],
        "category": "Income",
        "subcategory": "Cashback"
    },
    "refund": {
        "patterns": [
            r"refund",
            r"reversal",
            r"cancelled.*transaction",
        ],
        "category": "Income",
        "subcategory": "Refund"
    },
    "credit_card_payment": {
        "patterns": [
            r"cc\s*payment",
            r"credit\s*card\s*payment",
            r"card\s*bill",
        ],
        "category": "Financial",
        "subcategory": "Credit Card Bill"
    },
    "sip": {
        "patterns": [
            r"sip",
            r"systematic\s*investment",
            r"mutual\s*fund",
            r"mf\s*purchase",
        ],
        "category": "Financial",
        "subcategory": "SIP"
    },
    "insurance": {
        "patterns": [
            r"insurance",
            r"premium",
            r"prem\s*payment",
        ],
        "category": "Financial",
        "subcategory": "Insurance Premium"
    },
}


def compile_bank_patterns():
    """Compile all bank transaction patterns for efficient matching."""
    compiled = {}
    for pattern_name, pattern_data in BANK_PATTERNS.items():
        compiled[pattern_name] = {
            "regex": [re.compile(p, re.IGNORECASE) for p in pattern_data["patterns"]],
            "category": pattern_data["category"],
            "subcategory": pattern_data["subcategory"],
        }
    return compiled


COMPILED_BANK_PATTERNS = compile_bank_patterns()
