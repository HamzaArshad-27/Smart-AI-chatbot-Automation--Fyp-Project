from apps.ai_assistant.services.ollama_client import OllamaClient

VALID_INTENTS = {
    "SHOW_CATEGORIES",
    "SEARCH_PRODUCTS", 
    "SELECT_CATEGORY",
    "SHOW_FEATURED",
    "ASK_CLARIFICATION",
    "CHITCHAT",
    "UNKNOWN",
}


def classify_user_intent(message, history=None, awaiting_category=False):
    """Classify user intent with keyword fallback"""
    
    # First try quick keyword classification (always works)
    quick_result = _quick_classify(message, awaiting_category)
    
    # If it's clearly a product search, return immediately
    if quick_result["intent"] == "SEARCH_PRODUCTS":
        print(f"⚡ Quick classification: SEARCH_PRODUCTS")
        return quick_result
    
    # If it's a simple intent, return immediately
    if quick_result["intent"] in ["SHOW_CATEGORIES", "SHOW_FEATURED", "CHITCHAT", "ASK_CLARIFICATION"]:
        print(f"⚡ Quick classification: {quick_result['intent']}")
        return quick_result
    
    # Only use Ollama for complex cases
    try:
        client = OllamaClient()
        history_text = "\n".join(
            [f"User: {h.get('message', '')}\nAssistant: {h.get('response', '')}" for h in (history or [])[-4:]]
        ) or "No history."
        
        prompt = f"""Classify this user message for a shopping assistant.
Return ONLY JSON: {{"intent":"...","keyword":"...","category_hint":"..."}}

Options: SEARCH_PRODUCTS, ASK_CLARIFICATION, UNKNOWN.

User message: {message[:100]}
JSON:"""
        
        parsed = client.classify_with_prompt(prompt)
        intent = (parsed.get("intent") or "UNKNOWN").upper()
        
        if intent not in VALID_INTENTS:
            intent = "UNKNOWN"
        
        return {
            "intent": intent,
            "keyword": (parsed.get("keyword") or message)[:50],
            "category_hint": (parsed.get("category_hint") or "").strip(),
        }
    except Exception as e:
        print(f"❌ Ollama error, using fallback: {e}")
        return quick_result


def _quick_classify(message, awaiting_category=False):
    """Instant keyword-based classification with expanded product keywords"""
    msg = message.lower() if message else ""
    
    # If awaiting category, always treat as category selection
    if awaiting_category:
        return {"intent": "SELECT_CATEGORY", "keyword": message, "category_hint": message}
    
    # EXPANDED product keywords - add more categories
    product_keywords = [
        # Electronics
        "laptop", "phone", "mobile", "smartphone", "tablet", "ipad", "iphone", "android",
        "headphone", "earphone", "speaker", "soundbar", "tv", "television", "monitor",
        "keyboard", "mouse", "printer", "scanner", "router", "modem", "cable",
        "charger", "power bank", "battery", "adapter", "usb", "hdmi",
        
        # Clothing
        "shirt", "t-shirt", "tshirt", "pants", "jeans", "jacket", "coat", "sweater",
        "hoodie", "dress", "skirt", "shorts", "trousers", "blazer", "suit", "tie",
        "belt", "hat", "cap", "gloves", "scarf", "socks", "underwear", "lingerie",
        
        # Shoes
        "shoes", "sneakers", "boots", "sandals", "heels", "flip flops", "loafers",
        
        # Bags & Accessories
        "bag", "backpack", "purse", "wallet", "handbag", "luggage", "suitcase",
        "watch", "jewelry", "necklace", "ring", "bracelet", "earrings",
        
        # Home & Furniture
        "chair", "desk", "table", "bed", "sofa", "couch", "cabinet", "shelf",
        "lamp", "light", "curtain", "rug", "carpet", "pillow", "blanket",
        
        # Kitchen
        "pan", "pot", "knife", "cutting board", "blender", "mixer", "toaster",
        "microwave", "oven", "fridge", "refrigerator", "dishwasher",
        
        # Sports & Fitness
        "ball", "bat", "racket", "skateboard", "bicycle", "bike", "treadmill",
        "weights", "dumbbell", "yoga", "mat", "helmet", "pad",
        
        # Vehicles (ADD THESE)
        "car", "vehicle", "auto", "automobile", "truck", "suv", "sedan", "coupe",
        "convertible", "hatchback", "wagon", "van", "minivan", "pickup", "jeep",
        "motorcycle", "bike", "scooter", "electric vehicle", "ev", "hybrid",
        
        # Categories
        "electronics", "clothing", "fashion", "home", "garden", "sports",
        "outdoor", "beauty", "health", "toys", "games", "books", "music",
        "movies", "gaming", "computer", "accessories", "furniture",
        
        # Generic
        "product", "item", "stuff", "things", "goods", "merchandise"
    ]
    
    # Check for any product keyword
    if any(kw in msg for kw in product_keywords):
        # Extract the actual keyword
        keyword = message
        for kw in product_keywords:
            if kw in msg:
                keyword = kw
                break
        return {"intent": "SEARCH_PRODUCTS", "keyword": keyword, "category_hint": ""}
    
    # Check for categories
    if any(w in msg for w in ["category", "list", "browse", "what do you have", "show all", "show me"]):
        return {"intent": "SHOW_CATEGORIES", "keyword": "", "category_hint": ""}
    
    # Check for featured
    if any(w in msg for w in ["featured", "popular", "trending", "top", "best selling", "recommend"]):
        return {"intent": "SHOW_FEATURED", "keyword": "", "category_hint": ""}
    
    # Check for chitchat
    chitchat_words = ["hello", "hi", "hey", "good morning", "good evening", "how are you", 
                      "what's up", "sup", "yo", "greetings"]
    if any(w in msg for w in chitchat_words):
        return {"intent": "CHITCHAT", "keyword": "", "category_hint": ""}
    
    # Check for clarification needed
    if any(w in msg for w in ["gift", "suggest", "recommend", "help me", "what should"]):
        return {"intent": "ASK_CLARIFICATION", "keyword": "", "category_hint": ""}
    
    # Default: treat as search
    return {"intent": "SEARCH_PRODUCTS", "keyword": message, "category_hint": ""}