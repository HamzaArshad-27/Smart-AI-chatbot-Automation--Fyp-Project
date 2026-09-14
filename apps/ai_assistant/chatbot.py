import hashlib
import random
import re
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q

from apps.ai_assistant.graph import build_assistant_graph
from apps.ai_assistant.models import ChatHistory
from apps.ai_assistant.json_trainer import trainer
from apps.ai_assistant.ai_response import ai_response

RECENT_HISTORY_LIMIT = 6
CACHE_TTL_SECONDS = 3600
assistant_graph = build_assistant_graph()


# ============== NATURAL LANGUAGE PATTERNS ==============
GREETING_PATTERNS = [
    r'\b(hi|hello|hey|howdy|greetings|yo|sup|what\'s up|how are you|how r u|kese ho|kaise ho|salam|adaab)\b'
]

FAREWELL_PATTERNS = [
    r'\b(bye|goodbye|see you|later|take care|allah hafiz|khuda hafiz)\b'
]

THANK_YOU_PATTERNS = [
    r'\b(thanks|thank you|thx|shukriya|thank u|ty)\b'
]

HELP_PATTERNS = [
    r'\b(help|what can you do|how to use|assist me|help me)\b'
]

NAME_PATTERNS = [
    r'\b(what is your name|who are you|your name|tell me about yourself)\b'
]

CATEGORY_PATTERNS = [
    r'\b(categories?|sections?|types?|kinds?|what do you have|show me categories)\b'
]

STATS_PATTERNS = [
    r'\b(how many|total|count|number of|kitne|kull)\b.*\b(products?|items?|categories?)\b'
]

TRENDING_PATTERNS = [
    r'\b(trending|popular|top|best selling|mashoor|most sold)\b'
]

FEATURED_PATTERNS = [
    r'\b(featured|special|recommended|picks)\b'
]

CHITCHAT_PATTERNS = [
    r'\b(how are you|what\'s up|how do you do|how\'s it going)\b'
]

# Words that indicate product search (should not be treated as chitchat)
PRODUCT_INDICATORS = [
    'show', 'find', 'get', 'need', 'want', 'looking', 'search', 'give', 'buy',
    'purchase', 'order', 'have', 'clothing', 'clothes', 'vehicle', 'vehicles',
    'car', 'cars', 'shoes', 'laptop', 'phone', 'watch', 'bag', 'bags',
    'electronics', 'jewelry', 'furniture', 'accessories', 'sports', 'gaming',
    'product', 'item', 'items', 'jeans', 'shirt', 'jacket', 'dress', 'sweater',
    'sneakers', 'boots', 'tablet', 'computer', 'chair', 'desk', 'table', 'sofa'
]


def detect_intent(message: str) -> dict:
    """Detect the intent of the user message using regex patterns"""
    msg = message.lower().strip()
    
    # Check for product indicators first
    has_product_indicator = any(word in msg for word in PRODUCT_INDICATORS)
    
    # Check for empty/short messages that are not product searches
    if len(msg) <= 3 and not has_product_indicator:
        return {"intent": "chitchat", "confidence": 0.9}
    
    # Check for greetings
    if any(re.search(pattern, msg) for pattern in GREETING_PATTERNS):
        # But if it also has product indicators, treat as product search
        if has_product_indicator and len(msg) > 5:
            return {"intent": "product_search", "confidence": 0.8}
        return {"intent": "greeting", "confidence": 0.95}
    
    # Check for farewells
    if any(re.search(pattern, msg) for pattern in FAREWELL_PATTERNS):
        return {"intent": "farewell", "confidence": 0.95}
    
    # Check for thank you
    if any(re.search(pattern, msg) for pattern in THANK_YOU_PATTERNS):
        return {"intent": "thank_you", "confidence": 0.95}
    
    # Check for help
    if any(re.search(pattern, msg) for pattern in HELP_PATTERNS):
        return {"intent": "help", "confidence": 0.95}
    
    # Check for name
    if any(re.search(pattern, msg) for pattern in NAME_PATTERNS):
        return {"intent": "name", "confidence": 0.95}
    
    # Check for chitchat
    if any(re.search(pattern, msg) for pattern in CHITCHAT_PATTERNS):
        if has_product_indicator and len(msg) > 10:
            return {"intent": "product_search", "confidence": 0.7}
        return {"intent": "chitchat", "confidence": 0.85}
    
    # Check for categories
    if any(re.search(pattern, msg) for pattern in CATEGORY_PATTERNS):
        return {"intent": "categories", "confidence": 0.95}
    
    # Check for stats
    if any(re.search(pattern, msg) for pattern in STATS_PATTERNS):
        return {"intent": "stats", "confidence": 0.95}
    
    # Check for trending
    if any(re.search(pattern, msg) for pattern in TRENDING_PATTERNS):
        return {"intent": "trending", "confidence": 0.95}
    
    # Check for featured
    if any(re.search(pattern, msg) for pattern in FEATURED_PATTERNS):
        return {"intent": "featured", "confidence": 0.95}
    
    # If it has product indicators, search for products
    if has_product_indicator or len(msg) > 3:
        return {"intent": "product_search", "confidence": 0.7}
    
    # Default
    return {"intent": "chitchat", "confidence": 0.5}


def extract_search_term(message: str) -> str:
    """Extract the actual search term from the message"""
    msg = message.lower().strip()
    
    # Remove common question words
    remove_words = [
        'show', 'find', 'get', 'need', 'want', 'looking', 'search', 'give', 
        'buy', 'purchase', 'order', 'have', 'me', 'some', 'the', 'for', 'of',
        'and', 'or', 'but', 'with', 'without', 'please', 'can', 'could', 'would',
        'i', 'you', 'we', 'they', 'he', 'she', 'it', 'my', 'your', 'our', 'their'
    ]
    
    words = msg.split()
    search_words = []
    
    for word in words:
        # Remove punctuation
        word = re.sub(r'[^\w\s]', '', word)
        if word and len(word) > 1 and word not in remove_words:
            # Check if it's a product keyword
            for keyword in PRODUCT_INDICATORS:
                if word in keyword or keyword in word:
                    search_words.append(word)
                    break
            else:
                # If not a product keyword, still add if it's a noun-like word
                if len(word) > 2:
                    search_words.append(word)
    
    if not search_words:
        return message
    
    return " ".join(search_words[:3])  # Limit to 3 words


def get_natural_response(message: str, intent: dict) -> dict:
    """Generate natural response based on intent"""
    msg = message.lower().strip()
    
    # ===== GREETINGS =====
    if intent["intent"] == "greeting":
        greetings = [
            "Hello! 👋 How can I help you shop today?",
            "Hi there! Welcome to Vendora. What brings you here?",
            "Hey! Looking for something special today?",
            "Greetings! Ready to find some great products?",
            "Hello! 😊 What can I help you find today?"
        ]
        return {"response": random.choice(greetings), "suggestions": []}
    
    # ===== FAREWELL =====
    if intent["intent"] == "farewell":
        farewells = [
            "Goodbye! 👋 Come back anytime you need shopping help!",
            "Bye! Have a great day and happy shopping! 🛍️",
            "See you later! Remember, I'm always here to help you find products.",
            "Take care! 😊 Come back soon!"
        ]
        return {"response": random.choice(farewells), "suggestions": []}
    
    # ===== THANK YOU =====
    if intent["intent"] == "thank_you":
        thanks = [
            "You're welcome! 😊 Is there anything else I can help with?",
            "Happy to help! Let me know if you need anything else!",
            "My pleasure! Anytime you need shopping assistance, I'm here. 🌟",
            "You're most welcome! What else can I do for you today?"
        ]
        return {"response": random.choice(thanks), "suggestions": []}
    
    # ===== HELP =====
    if intent["intent"] == "help":
        return {
            "response": "I'm here to help! 🤖\n\nI can:\n• 🔍 Search for products (e.g., 'show me laptops')\n• 📂 Show categories (e.g., 'what are your categories')\n• 🔥 Show trending products (e.g., 'trending products')\n• ⭐ Show featured products (e.g., 'featured products')\n• 💬 Chat naturally with you\n\nWhat would you like to do?",
            "suggestions": []
        }
    
    # ===== NAME =====
    if intent["intent"] == "name":
        names = [
            "I'm Vendora AI, your personal shopping assistant! 🤖",
            "You can call me Vendora! I'm your AI shopping guide.",
            "I'm Vendora - your friendly AI shopping assistant at your service! 🌟",
            "I'm Vendora! Think of me as your digital shopping buddy. 🛍️"
        ]
        return {"response": random.choice(names), "suggestions": []}
    
    # ===== CHITCHAT =====
    if intent["intent"] == "chitchat":
        chitchats = [
            "That's interesting! 😊 How can I help you shop today?",
            "I see! What kind of products are you looking for?",
            "Got it! Is there anything specific I can help you find?",
            "I'm here to assist you! What products are you interested in?",
            "Hmm, interesting! Tell me what you're looking for and I'll help you find it. 🔍"
        ]
        return {"response": random.choice(chitchats), "suggestions": []}
    
    # ===== CATEGORIES =====
    if intent["intent"] == "categories":
        stats = trainer.get_stats()
        categories = stats.get('categories', [])
        if categories:
            cat_list = ", ".join(categories[:10])
            return {
                "response": f"📂 We have these categories in our store:\n\n{cat_list}\n\nWhich category are you interested in?",
                "suggestions": []
            }
        return {"response": "We have various categories including Electronics, Clothing, and more!", "suggestions": []}
    
    # ===== STATS =====
    if intent["intent"] == "stats":
        stats = trainer.get_stats()
        return {
            "response": f"📊 Welcome to Vendora!\n\nWe have {stats['total_products']} products in {stats['total_categories']} categories.\n\nHow can I help you today?",
            "suggestions": []
        }
    
    # ===== TRENDING =====
    if intent["intent"] == "trending":
        trending = trainer.get_trending(5)
        if trending:
            product_list = "\n".join([
                f"• {p['name']} - ${p['price']}"
                for p in trending[:5]
            ])
            return {
                "response": f"🔥 Our trending products right now:\n\n{product_list}\n\nWould you like more details about any of these?",
                "suggestions": trending[:5]
            }
        return {"response": "I couldn't find any trending products right now. Check our homepage for featured items!", "suggestions": []}
    
    # ===== FEATURED =====
    if intent["intent"] == "featured":
        featured = trainer.get_featured(5)
        if featured:
            product_list = "\n".join([
                f"• {p['name']} - ${p['price']}"
                for p in featured[:5]
            ])
            return {
                "response": f"⭐ Our featured products:\n\n{product_list}\n\nWould you like to see more?",
                "suggestions": featured[:5]
            }
        return {"response": "We have many great products! Which category interests you?", "suggestions": []}
    
    # ===== PRODUCT SEARCH =====
    if intent["intent"] == "product_search":
        # Extract search term
        search_term = extract_search_term(message)
        
        # If search term is too short or generic, ask for clarification
        if not search_term or len(search_term) < 2:
            return {
                "response": "What kind of product are you looking for? 🤔\n\nTry being more specific like:\n• 'show me laptops'\n• 'i need shoes'\n• 'looking for a watch'",
                "suggestions": []
            }
        
        # Search for products
        results = trainer.search(search_term, 5)
        
        if results:
            product_list = "\n".join([
                f"• {p['name']} - ${p['price']}"
                for p in results[:5]
            ])
            return {
                "response": f"🔍 Here are products matching '{search_term}':\n\n{product_list}\n\nClick on any product to view details.",
                "suggestions": results[:5]
            }
        else:
            # Try to find by category
            categories = trainer.get_stats().get('categories', [])
            found_products = []
            for cat in categories:
                if any(word in search_term for word in cat.lower().split()):
                    found_products = trainer.get_products_by_category(cat)
                    if found_products:
                        break
            
            if found_products:
                product_list = "\n".join([
                    f"• {p['name']} - ${p['price']}"
                    for p in found_products[:5]
                ])
                return {
                    "response": f"I couldn't find exactly '{search_term}', but here are some products from our store:\n\n{product_list}\n\nWould you like to see more?",
                    "suggestions": found_products[:5]
                }
            
            # Random fallback products
            random_products = trainer.get_random_products(3)
            if random_products:
                product_list = "\n".join([
                    f"• {p['name']} - ${p['price']}"
                    for p in random_products[:3]
                ])
                return {
                    "response": f"I couldn't find products matching '{search_term}'. 😕\n\nHere are some popular items you might like:\n\n{product_list}\n\nOr try:\n• 'show me categories'\n• 'trending products'",
                    "suggestions": random_products[:3]
                }
            
            return {
                "response": f"I couldn't find any products matching '{search_term}'. 😕\n\nTry:\n• Using different keywords\n• Asking for 'categories'\n• Checking 'trending products'",
                "suggestions": []
            }
    
    # ===== FALLBACK =====
    return {
        "response": "I'm here to help you shop! 🛍️\n\nTry asking:\n• 'show me laptops'\n• 'what are your categories'\n• 'trending products'\n\nWhat would you like to know?",
        "suggestions": []
    }


def _cache_key(user_id, message):
    msg_hash = hashlib.md5(message.strip().lower().encode()).hexdigest()
    return f"ai_graph_chat:{user_id}:{msg_hash}"


def _load_recent_messages(user):
    rows = (
        ChatHistory.objects.filter(user=user)
        .order_by("-created_at")
        .values("message", "response")[:RECENT_HISTORY_LIMIT]
    )
    rows = list(reversed(list(rows)))
    messages = []
    for row in rows:
        messages.append({"role": "user", "content": row.get("message", "")})
        messages.append({"role": "assistant", "content": row.get("response", "")})
    return messages


# ============== MAIN PROCESS FUNCTION ==============
def process_chat_message(user, message, graph_state=None):
    normalized = (message or "").strip()
    if not normalized:
        return {"response": "Please type a message.", "suggestions": []}, graph_state or {}

    # Check cache first
    cache_key = _cache_key(user.id, normalized)
    cached = cache.get(cache_key)
    if cached:
        ChatHistory.objects.create(
            user=user,
            message=normalized,
            response=cached.get("response", ""),
            context_used={"source": "cache", "suggestions": cached.get("suggestions", [])},
        )
        return cached, (graph_state or {})

    state = graph_state or {}
    messages = state.get("messages") or _load_recent_messages(user)
    messages.append({"role": "user", "content": normalized})
    
    print(f"💬 Processing: {normalized}")
    
    # ===== DETECT INTENT =====
    intent = detect_intent(normalized)
    print(f"🎯 Detected intent: {intent['intent']} (confidence: {intent['confidence']})")
    
    # ===== GENERATE RESPONSE =====
    result = get_natural_response(normalized, intent)
    response_text = result.get("response", "")
    suggestions = result.get("suggestions", [])
    
    payload = {"response": response_text, "suggestions": suggestions}
    
    persisted_state = {
        "messages": messages + [{"role": "assistant", "content": response_text}],
        "step": "initial",
        "selected_category_id": None,
        "last_search_keyword": normalized,
        "categories_shown": False,
    }
    
    # Save to database
    ChatHistory.objects.create(
        user=user,
        message=normalized,
        response=response_text,
        context_used={
            "intent": intent['intent'],
            "confidence": intent['confidence'],
        },
    )
    
    # Cache the response
    cache.set(cache_key, payload, CACHE_TTL_SECONDS)
    
    return payload, persisted_state