# apps/ai_assistant/entity_extractor.py
"""
Rule-based entity extraction for shopping queries.
Extracts price ranges, brands, categories, colors, and sizes from user messages.
"""

import re
from typing import Dict, Any, List, Optional


# ─── Known entity dictionaries ───────────────────────────────────────────────

KNOWN_COLORS = {
    "red", "blue", "green", "black", "white", "yellow", "purple", "pink",
    "orange", "brown", "grey", "gray", "silver", "gold", "navy", "beige",
    "maroon", "teal", "coral", "ivory", "cream", "burgundy", "olive",
    "cyan", "magenta", "turquoise", "lavender", "indigo", "khaki",
}

KNOWN_SIZES = {
    "xs", "s", "m", "l", "xl", "xxl", "xxxl",
    "extra small", "small", "medium", "large", "extra large",
    "6", "7", "8", "9", "10", "11", "12", "13", "14",
    "28", "30", "32", "34", "36", "38", "40", "42",
}

# Common brands across categories — extend as needed from your product data
KNOWN_BRANDS = {
    "nike", "adidas", "puma", "reebok", "new balance", "under armour",
    "samsung", "apple", "sony", "lg", "dell", "hp", "lenovo", "asus",
    "gucci", "zara", "h&m", "levi", "levis", "levi's",
    "toyota", "honda", "suzuki", "yamaha", "kawasaki",
    "loreal", "l'oreal", "nivea", "dove", "garnier", "maybelline",
    "nestle", "unilever", "p&g", "colgate", "gillette",
}

# Category aliases — maps casual terms to standard category names
CATEGORY_ALIASES = {
    # Accessories
    "accessories": "Accessories", "accessory": "Accessories",
    "watch": "Accessories", "watches": "Accessories",
    "jewelry": "Accessories", "jewellery": "Accessories",
    "bracelet": "Accessories", "necklace": "Accessories",
    "sunglasses": "Accessories", "belt": "Accessories", "belts": "Accessories",
    "wallet": "Accessories", "wallets": "Accessories",
    "bag": "Accessories", "bags": "Accessories", "handbag": "Accessories",
    "purse": "Accessories", "backpack": "Accessories",
    # Automotive
    "automotive": "Automotive", "car": "Automotive", "cars": "Automotive",
    "auto": "Automotive", "automobile": "Automotive",
    "bike": "Automotive", "motorcycle": "Automotive",
    # Beauty Health
    "beauty": "Beauty Health", "health": "Beauty Health",
    "skincare": "Beauty Health", "skin care": "Beauty Health",
    "makeup": "Beauty Health", "cosmetics": "Beauty Health",
    "perfume": "Beauty Health", "fragrance": "Beauty Health",
    "haircare": "Beauty Health", "hair care": "Beauty Health",
    "shampoo": "Beauty Health", "lotion": "Beauty Health",
    # Clothing
    "clothing": "Clothing", "clothes": "Clothing", "apparel": "Clothing",
    "shirt": "Clothing", "shirts": "Clothing",
    "t-shirt": "Clothing", "tshirt": "Clothing", "tee": "Clothing",
    "pants": "Clothing", "jeans": "Clothing", "trousers": "Clothing",
    "dress": "Clothing", "dresses": "Clothing",
    "jacket": "Clothing", "jackets": "Clothing", "coat": "Clothing",
    "sweater": "Clothing", "hoodie": "Clothing", "hoodies": "Clothing",
    "skirt": "Clothing", "shorts": "Clothing",
    "suit": "Clothing", "suits": "Clothing",
    "formal wear": "Clothing", "casual wear": "Clothing",
    # Grocery Food
    "grocery": "Grocery Food", "groceries": "Grocery Food",
    "food": "Grocery Food", "snacks": "Grocery Food", "snack": "Grocery Food",
    "drinks": "Grocery Food", "beverages": "Grocery Food",
    # Mobiles Tablets
    "mobile": "Mobiles Tablets", "mobiles": "Mobiles Tablets",
    "phone": "Mobiles Tablets", "phones": "Mobiles Tablets",
    "smartphone": "Mobiles Tablets", "smartphones": "Mobiles Tablets",
    "tablet": "Mobiles Tablets", "tablets": "Mobiles Tablets",
    "ipad": "Mobiles Tablets", "iphone": "Mobiles Tablets",
    "android": "Mobiles Tablets", "cell phone": "Mobiles Tablets",
    # Sports Outdoors
    "sports": "Sports Outdoors", "sport": "Sports Outdoors",
    "outdoors": "Sports Outdoors", "outdoor": "Sports Outdoors",
    "fitness": "Sports Outdoors", "gym": "Sports Outdoors",
    "exercise": "Sports Outdoors", "workout": "Sports Outdoors",
    "running": "Sports Outdoors", "cycling": "Sports Outdoors",
    "camping": "Sports Outdoors", "hiking": "Sports Outdoors",
    "yoga": "Sports Outdoors",
    "shoes": "Sports Outdoors", "shoe": "Sports Outdoors",
    "sneakers": "Sports Outdoors", "trainers": "Sports Outdoors",
    "boots": "Sports Outdoors",
    # Toys Games
    "toys": "Toys Games", "toy": "Toys Games",
    "games": "Toys Games", "game": "Toys Games",
    "puzzle": "Toys Games", "puzzles": "Toys Games",
    "board game": "Toys Games", "action figure": "Toys Games",
    "doll": "Toys Games", "dolls": "Toys Games",
    "lego": "Toys Games",
    # Vehicles
    "vehicle": "Vehicles", "vehicles": "Vehicles",
    "truck": "Vehicles", "van": "Vehicles",
    "suv": "Vehicles", "sedan": "Vehicles",
}


# ─── Price extraction patterns ──────────────────────────────────────────────

PRICE_PATTERNS = [
    # "under $50", "below $50", "less than $50", "cheaper than $50"
    (r'(?:under|below|less\s+than|cheaper\s+than|max|maximum|up\s+to|upto)\s*\$?\s*(\d+(?:\.\d+)?)', 'max'),
    # "over $50", "above $50", "more than $50", "at least $50", "minimum $50"
    (r'(?:over|above|more\s+than|at\s+least|min|minimum|from|starting)\s*\$?\s*(\d+(?:\.\d+)?)', 'min'),
    # "between $20 and $50", "$20-$50", "$20 to $50"
    (r'\$?\s*(\d+(?:\.\d+)?)\s*(?:to|-|and)\s*\$?\s*(\d+(?:\.\d+)?)', 'range'),
    # "$50" standalone
    (r'\$\s*(\d+(?:\.\d+)?)', 'exact'),
    # "50 dollars", "50 rupees", "50 bucks"
    (r'(\d+(?:\.\d+)?)\s*(?:dollars?|bucks?|rupees?|rs\.?|pkr)', 'exact'),
]


def extract_entities(message: str) -> Dict[str, Any]:
    """
    Extract structured entities from a user message.

    Returns:
        {
            "price_min": float or None,
            "price_max": float or None,
            "brands": [str],
            "categories": [str],
            "colors": [str],
            "sizes": [str],
            "raw_query": str  # message with entities stripped for product search
        }
    """
    msg = message.lower().strip()
    result = {
        "price_min": None,
        "price_max": None,
        "brands": [],
        "categories": [],
        "colors": [],
        "sizes": [],
        "raw_query": msg,
    }

    # ─── Extract price ────────────────────────────────────────────────
    _extract_price(msg, result)

    # ─── Extract colors ──────────────────────────────────────────────
    words = set(re.findall(r'\b\w+\b', msg))
    found_colors = words & KNOWN_COLORS
    if found_colors:
        result["colors"] = sorted(found_colors)

    # ─── Extract sizes ───────────────────────────────────────────────
    for size in KNOWN_SIZES:
        # Match whole word or whole phrase
        pattern = rf'\b{re.escape(size)}\b'
        if re.search(pattern, msg):
            result["sizes"].append(size)

    # ─── Extract brands ──────────────────────────────────────────────
    for brand in KNOWN_BRANDS:
        pattern = rf'\b{re.escape(brand)}\b'
        if re.search(pattern, msg):
            result["brands"].append(brand)

    # ─── Extract categories ──────────────────────────────────────────
    _extract_categories(msg, result)

    # ─── Build raw query (strip entities for cleaner search) ─────────
    result["raw_query"] = _build_raw_query(msg, result)

    return result


def _extract_price(msg: str, result: Dict) -> None:
    """Extract price range from message."""
    for pattern, price_type in PRICE_PATTERNS:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            if price_type == 'range':
                val1 = float(match.group(1))
                val2 = float(match.group(2))
                result["price_min"] = min(val1, val2)
                result["price_max"] = max(val1, val2)
            elif price_type == 'max':
                result["price_max"] = float(match.group(1))
            elif price_type == 'min':
                result["price_min"] = float(match.group(1))
            elif price_type == 'exact':
                # Treat exact price as approximate: ±20%
                exact = float(match.group(1))
                result["price_min"] = exact * 0.8
                result["price_max"] = exact * 1.2
            return  # Take first match only


def _extract_categories(msg: str, result: Dict) -> None:
    """Extract category names from message using alias mapping."""
    found = set()
    # Sort by length descending so "board game" matches before "game"
    sorted_aliases = sorted(CATEGORY_ALIASES.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        pattern = rf'\b{re.escape(alias)}\b'
        if re.search(pattern, msg):
            canonical = CATEGORY_ALIASES[alias]
            if canonical not in found:
                found.add(canonical)
                result["categories"].append(canonical)


def _build_raw_query(msg: str, result: Dict) -> str:
    """Strip known entities from message to get the core search query."""
    raw = msg

    # Remove price patterns
    for pattern, _ in PRICE_PATTERNS:
        raw = re.sub(pattern, '', raw, flags=re.IGNORECASE)

    # Remove filler words
    filler = [
        'show', 'find', 'get', 'need', 'want', 'looking', 'search', 'give',
        'buy', 'purchase', 'order', 'have', 'me', 'some', 'the', 'for', 'of',
        'and', 'or', 'but', 'with', 'without', 'please', 'can', 'could',
        'would', 'i', 'you', 'we', 'they', 'my', 'your', 'a', 'an', 'in',
        'do', 'does', 'any', 'all', 'is', 'are', 'to', 'that', "i'm",
        'looking for', 'show me', 'i need', 'i want', 'can you',
    ]
    for word in sorted(filler, key=len, reverse=True):
        raw = re.sub(rf'\b{re.escape(word)}\b', '', raw, flags=re.IGNORECASE)

    # Remove dollar signs and leftover punctuation
    raw = re.sub(r'[$]', '', raw)
    raw = re.sub(r'\s+', ' ', raw).strip()

    return raw if raw else msg


def has_entities(entities: Dict) -> bool:
    """Check if any meaningful entities were extracted."""
    return bool(
        entities.get("price_min") is not None
        or entities.get("price_max") is not None
        or entities.get("brands")
        or entities.get("categories")
        or entities.get("colors")
        or entities.get("sizes")
    )


def summarize_entities(entities: Dict) -> str:
    """Human-readable summary of extracted entities for context injection."""
    parts = []
    if entities.get("categories"):
        parts.append(f"Categories: {', '.join(entities['categories'])}")
    if entities.get("brands"):
        parts.append(f"Brands: {', '.join(entities['brands'])}")
    if entities.get("price_min") is not None and entities.get("price_max") is not None:
        parts.append(f"Price range: ${entities['price_min']:.0f} - ${entities['price_max']:.0f}")
    elif entities.get("price_max") is not None:
        parts.append(f"Max price: ${entities['price_max']:.0f}")
    elif entities.get("price_min") is not None:
        parts.append(f"Min price: ${entities['price_min']:.0f}")
    if entities.get("colors"):
        parts.append(f"Colors: {', '.join(entities['colors'])}")
    if entities.get("sizes"):
        parts.append(f"Sizes: {', '.join(entities['sizes'])}")
    return " | ".join(parts) if parts else ""
