# apps/ai_assistant/chatbot.py
"""
Vendora AI Shopping Assistant - Main Orchestration Engine.

Implements Retrieval-Augmented Generation (RAG) with:
- Intent classification and rule-based entity extraction (price, brand, category, color)
- Hybrid search (FAISS semantic vectors + PostgreSQL FTS + entity filtering + user personalization)
- Context-grounded LLM response generation via Ollama
- Hallucination verification & fact-checking
- Adaptive context-aware quick replies
- Dynamic fallback mechanisms for zero downtime
"""

import hashlib
import json
import logging
import random
import re
from typing import Dict, Any, List, Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from apps.ai_assistant.models import ChatHistory, UserChatPreference, UserProductInterest
from apps.ai_assistant.json_trainer import trainer
from apps.ai_assistant.data_loader import WebsiteDataLoader
from apps.ai_assistant.services.ollama_client import OllamaClient
from apps.ai_assistant.services.product_retrieval import hybrid_search, serialize_product
from apps.ai_assistant.services.embedding_service import embedding_service
from apps.ai_assistant.entity_extractor import extract_entities, has_entities, summarize_entities
from apps.ai_assistant.persona import (
    VENDORA_SYSTEM_PROMPT,
    VENDORA_PRODUCT_PROMPT,
    VENDORA_CHITCHAT_PROMPT,
    GREETING_RESPONSES,
    FAREWELL_RESPONSES,
    THANKS_RESPONSES,
    HOW_ARE_YOU_RESPONSES,
    IDENTITY_RESPONSES,
    HELP_RESPONSE,
)
from apps.ai_assistant.verifier import verify_response, build_product_context
from apps.ai_assistant.ai_response import AIResponseGenerator

logger = logging.getLogger(__name__)

RECENT_HISTORY_LIMIT = 6
CACHE_TTL_SECONDS = 1800  # 30 minutes cache for rapid repeated queries
ollama_client = OllamaClient()


# ==============================================================================
# 1. ADAPTIVE QUICK REPLIES
# ==============================================================================

def get_quick_replies(
    intent: Optional[str] = None,
    products: Optional[List[Dict]] = None,
    entities: Optional[Dict] = None,
    last_response: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Generate dynamic, context-aware quick reply chips based on intent,
    retrieved products, extracted entities, and recent context.
    """
    replies = []
    entities = entities or {}
    products = products or []

    # 1. If products were returned in search/recommendations
    if products and len(products) > 0:
        # Category exploration chip
        cat = products[0].get("category") or products[0].get("category_name")
        if cat:
            replies.append({"label": f"📂 More in {cat}", "message": f"show more {cat}"})

        # Price refinement chip
        prices = []
        for p in products:
            try:
                prices.append(float(p.get("price", 0)))
            except (ValueError, TypeError):
                pass

        if prices:
            median_price = sorted(prices)[len(prices) // 2]
            if median_price > 20:
                under_val = int(median_price)
                replies.append({"label": f"💰 Under ${under_val}", "message": f"under ${under_val}"})

        replies.append({"label": "⭐ Top Rated", "message": "show top rated"})
        replies.append({"label": "🔥 Trending", "message": "trending products"})
        return replies[:4]

    # 2. If user is exploring categories or stats
    if intent in ["categories", "category_browse"]:
        stats = trainer.get_stats()
        cats = stats.get("categories", [])
        if cats:
            for c in cats[:3]:
                replies.append({"label": f"🛍️ {c}", "message": f"show me {c}"})
        replies.append({"label": "🔥 Trending", "message": "trending products"})
        return replies[:4]

    # 3. If user asked for stats or general help
    if intent in ["stats", "help"]:
        replies.append({"label": "📂 Categories", "message": "what are your categories"})
        replies.append({"label": "🔥 Trending Items", "message": "trending products"})
        replies.append({"label": "⭐ Featured", "message": "featured products"})
        replies.append({"label": "👟 Shoes", "message": "show me shoes"})
        return replies

    # 4. If chitchat / greeting
    if intent in ["chitchat", "greeting"]:
        replies.append({"label": "🔥 What's Trending?", "message": "trending products"})
        replies.append({"label": "📂 Browse Categories", "message": "what are your categories"})
        replies.append({"label": "🎁 Gift Ideas", "message": "recommend gift ideas under $50"})
        replies.append({"label": "⭐ Featured Picks", "message": "featured products"})
        return replies

    # 5. Default fallback quick replies
    return [
        {"label": "📂 Categories", "message": "what are your categories"},
        {"label": "🔥 Trending", "message": "trending products"},
        {"label": "⭐ Featured", "message": "featured products"},
        {"label": "❓ Help", "message": "help"},
    ]


# ==============================================================================
# 2. INTENT DETECTION & NLU
# ==============================================================================

def detect_intent(message: str) -> Dict[str, Any]:
    """
    Detect user intent using multi-layer heuristics and entity extraction.
    """
    msg = message.lower().strip()
    entities = extract_entities(message)

    # ── Shortcuts & UI Commands ──
    if any(k in msg for k in ["quick replies", "quick reply", "shortcuts", "menu"]):
        return {"intent": "show_quick_replies", "confidence": 0.99, "entities": entities}

    # ── Categories & Sections ──
    category_phrases = [
        "what are your categories", "show categories", "list categories",
        "all categories", "what categories", "sections", "departments",
        "browse categories", "categories"
    ]
    if any(phrase in msg for phrase in category_phrases) and not has_entities(entities):
        return {"intent": "categories", "confidence": 0.95, "entities": entities}

    # ── Store Stats ──
    stats_keywords = ["how many products", "total products", "store stats", "catalog size", "inventory count"]
    if any(k in msg for k in stats_keywords):
        return {"intent": "stats", "confidence": 0.95, "entities": entities}

    # ── Trending Products ──
    trending_phrases = ["trending", "popular right now", "best selling", "top seller", "most popular", "mashoor"]
    if any(p in msg for p in trending_phrases) and not entities.get("categories"):
        return {"intent": "trending", "confidence": 0.95, "entities": entities}

    # ── Featured Products ──
    featured_phrases = ["featured", "staff picks", "special picks", "recommended products", "today's specials"]
    if any(p in msg for p in featured_phrases) and not entities.get("categories"):
        return {"intent": "featured", "confidence": 0.95, "entities": entities}

    # ── Help / Capabilities ──
    help_phrases = ["help", "what can you do", "how do you work", "assist me", "instructions", "guide me"]
    if msg in help_phrases or (len(msg) < 15 and "help" in msg):
        return {"intent": "help", "confidence": 0.95, "entities": entities}

    # ── Conversational Greetings & Chitchat ──
    greeting_triggers = ["hello", "hi", "hey", "howdy", "greetings", "yo", "salam", "assalam", "adaab", "namaste"]
    farewell_triggers = ["bye", "goodbye", "see you", "later", "take care", "cya"]
    thanks_triggers = ["thank you", "thanks", "thx", "shukriya", "jazakallah", "appreciate it"]
    how_are_you_triggers = ["how are you", "how r u", "how's it going", "how are you doing", "kaise ho", "kese ho"]
    identity_triggers = ["who are you", "what is your name", "what's your name", "tell me about yourself", "are you an ai"]

    # If it's pure chitchat with no shopping entities
    if not has_entities(entities):
        words = set(re.findall(r'\b\w+\b', msg))
        if words & set(greeting_triggers) and len(words) <= 3:
            return {"intent": "greeting", "confidence": 0.95, "entities": entities}
        if any(f in msg for f in farewell_triggers) and len(words) <= 4:
            return {"intent": "farewell", "confidence": 0.95, "entities": entities}
        if any(t in msg for t in thanks_triggers) and len(words) <= 4:
            return {"intent": "thanks", "confidence": 0.95, "entities": entities}
        if any(h in msg for h in how_are_you_triggers):
            return {"intent": "how_are_you", "confidence": 0.95, "entities": entities}
        if any(i in msg for i in identity_triggers):
            return {"intent": "identity", "confidence": 0.95, "entities": entities}

        chitchat_general = [
            "good morning", "good evening", "good night", "what's up", "sup",
            "are you single", "what are you doing", "tell me a joke", "haha", "lol",
            "nice", "cool", "awesome", "great", "ok", "okay"
        ]
        if any(w in msg for w in chitchat_general):
            return {"intent": "chitchat", "confidence": 0.90, "entities": entities}

    # ── Category Browsing (if category explicitly mentioned without search verb) ──
    if entities.get("categories") and not any(v in msg for v in ["search", "find", "show me", "buy", "get", "need", "want"]):
        return {"intent": "category_browse", "confidence": 0.85, "entities": entities}

    # ── Default: Product Search with Entity Grounding ──
    return {"intent": "product_search", "confidence": 0.80, "entities": entities}


# ==============================================================================
# 3. RAG GROUNDED GENERATION WITH OLLAMA
# ==============================================================================

def generate_grounded_response(
    message: str,
    intent: Dict[str, Any],
    products: List[Dict],
    chat_history: Optional[List[Dict]] = None,
    user=None,
) -> str:
    """
    Generate a grounded, natural language response using Ollama LLM
    with retrieved product context and post-generation hallucination verification.
    """
    chat_history = chat_history or []
    intent_name = intent.get("intent", "product_search")
    entities = intent.get("entities", {})

    # Build Grounded Context
    context_lines = []
    
    # 1. Product Context
    if products:
        context_lines.append(build_product_context(products[:6]))
    else:
        context_lines.append("RETRIEVED PRODUCTS: None found directly matching all criteria.")

    # 2. Entity Constraints Summary
    entity_summary = summarize_entities(entities)
    if entity_summary:
        context_lines.append(f"USER SPECIFICATIONS: {entity_summary}")

    # 3. Store Statistics Context
    stats = trainer.get_stats()
    context_lines.append(
        f"STORE DATA: Total Products={stats.get('total_products', 0)}, Categories={', '.join(stats.get('categories', [])[:6])}"
    )

    full_context = "\n\n".join(context_lines)

    # Choose prompt based on query nature
    system_prompt = VENDORA_PRODUCT_PROMPT if products else VENDORA_SYSTEM_PROMPT

    try:
        result = ollama_client.generate_with_context(
            system_prompt=system_prompt,
            user_message=message,
            context=full_context,
            chat_history=chat_history,
            temperature=0.25,  # Low temperature to stick strictly to factual grounded products
            max_tokens=160,
        )

        reply = result.get("reply", "").strip()

        if reply:
            # Fact-check & verify LLM response against actual retrieved product data
            verified_reply = verify_response(reply, products)
            return verified_reply

    except Exception as e:
        logger.warning(f"Ollama generation failed or timed out: {e}")

    # Fallback to high-quality deterministic response if Ollama is unreachable
    return build_deterministic_response(message, intent, products)


# ==============================================================================
# 4. DETERMINISTIC FALLBACK RESPONSES
# ==============================================================================

def build_deterministic_response(
    message: str,
    intent: Dict[str, Any],
    products: List[Dict],
) -> str:
    """
    Reliable deterministic fallback response generator when Ollama is offline or unavailable.
    """
    intent_name = intent.get("intent", "product_search")
    entities = intent.get("entities", {})

    if intent_name == "show_quick_replies":
        return (
            "📱 **Quick Shortcuts:**\n\n"
            "• 📂 **Categories** → 'what are your categories'\n"
            "• 🔥 **Trending** → 'trending products'\n"
            "• ⭐ **Featured** → 'featured products'\n"
            "• 🔍 **Search** → 'show me shoes under $50'\n"
            "• ❓ **Help** → 'help'\n"
            "• 📊 **Store Stats** → 'how many products'\n\n"
            "You can click any chip below or type freely!"
        )

    if intent_name == "categories":
        stats = trainer.get_stats()
        categories = stats.get("categories", [])
        if categories:
            cat_list = ", ".join(categories[:10])
            return f"📂 We currently have these categories available in our store:\n\n**{cat_list}**\n\nWhich department would you like to explore?"
        return "We offer an extensive range of categories including Electronics, Clothing, Sports, Accessories, and more!"

    if intent_name == "stats":
        stats = trainer.get_stats()
        return (
            f"📊 **Welcome to Vendora!**\n\n"
            f"We have **{stats['total_products']} active products** spanning **{stats['total_categories']} departments**.\n\n"
            f"Looking for anything specific today?"
        )

    if intent_name == "trending":
        if products:
            product_list = "\n".join([f"• **{p['name']}** — ${p['price']}" for p in products[:5]])
            return f"🔥 Here are our most popular trending items right now:\n\n{product_list}\n\nWould you like more details on any of these?"
        return "Check out our featured collection on the homepage for popular picks!"

    if intent_name == "featured":
        if products:
            product_list = "\n".join([f"• **{p['name']}** — ${p['price']}" for p in products[:5]])
            return f"⭐ Here are our top featured recommendations:\n\n{product_list}\n\nLet me know if you'd like to narrow these down by price or style!"
        return "We have wonderful products throughout our catalog. What are you looking to buy?"

    if intent_name == "help":
        return HELP_RESPONSE

    if intent_name == "greeting":
        return random.choice(GREETING_RESPONSES)

    if intent_name == "farewell":
        return random.choice(FAREWELL_RESPONSES)

    if intent_name == "thanks":
        return random.choice(THANKS_RESPONSES)

    if intent_name == "how_are_you":
        return random.choice(HOW_ARE_YOU_RESPONSES)

    if intent_name == "identity":
        return random.choice(IDENTITY_RESPONSES)

    # Product search fallback
    if products:
        intros = [
            "Here are the best matches I found for you:",
            "I found some great options that fit what you're looking for:",
            "Take a look at these top matches from our store:",
        ]
        product_list = "\n".join([f"• **{p['name']}** — ${p['price']}" for p in products[:5]])
        follow_up = "\n\nWould you like me to filter these by price, brand, or category?"
        return f"{random.choice(intros)}\n\n{product_list}{follow_up}"

    # No products found
    raw_query = entities.get("raw_query") or message
    random_picks = trainer.get_random_products(3)
    if random_picks:
        pick_list = "\n".join([f"• **{p['name']}** — ${p['price']}" for p in random_picks])
        return (
            f"I couldn't find an exact match for '{raw_query}', but here are some popular items in our store:\n\n"
            f"{pick_list}\n\n"
            f"Try searching by category (e.g., 'shoes', 'accessories') or browse 'trending products'!"
        )

    return f"I couldn't find products matching '{raw_query}'. Try checking our categories or adjusting your search keywords!"


# ==============================================================================
# 5. USER PREFERENCES & RECOMMENDATIONS
# ==============================================================================

def update_user_preferences(user, message: str, products: Optional[List[Dict]] = None):
    """Record user interactions to refine future recommendations."""
    if not user or not user.is_authenticated:
        return

    # Track category mentions
    categories = trainer.get_stats().get("categories", [])
    msg_lower = message.lower()
    for cat in categories:
        if cat.lower() in msg_lower:
            AIResponseGenerator.track_user_interest(user, category=cat)
            break

    # Track product impressions
    if products:
        for p in products[:2]:
            pid = p.get("id")
            if pid:
                AIResponseGenerator.track_user_interest(user, product_id=pid)


def get_personalized_recommendations(user, limit: int = 3) -> List[Dict]:
    """Retrieve personalized product recommendations based on user history."""
    if not user or not user.is_authenticated:
        return []

    products = AIResponseGenerator.get_personalized_recommendations(user, limit)
    if products:
        return products

    return trainer.get_trending(limit)


# ==============================================================================
# 6. CACHE & CONVERSATION HISTORY
# ==============================================================================

def _cache_key(user_id, message: str) -> str:
    msg_hash = hashlib.md5(message.strip().lower().encode("utf-8")).hexdigest()
    return f"ai_rag_chat:{user_id}:{msg_hash}"


def _load_recent_messages(user) -> List[Dict[str, str]]:
    if not user or not user.is_authenticated:
        return []
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


# ==============================================================================
# 7. MAIN ORCHESTRATION PIPELINE (RAG ENTRY POINT)
# ==============================================================================

def process_chat_message(user, message: str, graph_state: Optional[Dict] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Main orchestration pipeline called by views.chat_api.

    Steps:
    1. Normalize input & check cache
    2. Load conversation history
    3. Detect intent & extract entities (NLU)
    4. Retrieve grounded candidates (FAISS semantic + FTS + DB filter + user rerank)
    5. Generate conversational response (Ollama + verification or deterministic fallback)
    6. Update user preferences
    7. Generate dynamic quick replies & suggestions
    8. Persist chat history and cache response
    """
    normalized = (message or "").strip()
    if not normalized:
        return {
            "response": "Please type a message so I can assist you.",
            "suggestions": [],
            "quick_replies": get_quick_replies(),
        }, graph_state or {}

    user_id = user.id if (user and user.is_authenticated) else "anonymous"
    cache_key = _cache_key(user_id, normalized)
    cached = cache.get(cache_key)

    # Return cached response if recently queried
    if cached:
        if user and user.is_authenticated:
            ChatHistory.objects.create(
                user=user,
                message=normalized,
                response=cached.get("response", ""),
                context_used={"source": "cache", "suggestions_count": len(cached.get("suggestions", []))},
            )
        return cached, (graph_state or {})

    # Conversation state & recent history
    state = graph_state or {}
    messages = state.get("messages") or _load_recent_messages(user)
    messages.append({"role": "user", "content": normalized})

    # Step 1: Detect Intent & Extract Entities
    intent_data = detect_intent(normalized)
    intent_name = intent_data["intent"]
    entities = intent_data.get("entities", {})

    logger.info(f"AI Assistant Processing: query='{normalized}' intent='{intent_name}'")

    # Step 2: Retrieve Relevant Products (Hybrid Search)
    products: List[Dict] = []

    if intent_name in ["product_search", "category_browse"]:
        search_query = entities.get("raw_query") or normalized
        # Perform hybrid search (FAISS + FTS + entity filtering + user personalization)
        products = hybrid_search(
            query=search_query,
            entities=entities,
            user=user,
            limit=5,
        )

        # Fallback if specific category was identified but no items returned
        if not products and entities.get("categories"):
            cat = entities["categories"][0]
            products = trainer.get_products_by_category(cat)[:5]

    elif intent_name == "trending":
        products = trainer.get_trending(5)
        if not products:
            products = WebsiteDataLoader.load_trending_products(5)

    elif intent_name == "featured":
        products = trainer.get_featured(5)

    # Step 3: Generate Grounded Response (Ollama with DB Context / Fallback)
    response_text = ""

    # Instant response for fast greetings when no products requested
    if intent_name == "greeting":
        response_text = random.choice(GREETING_RESPONSES)
    elif intent_name == "farewell":
        response_text = random.choice(FAREWELL_RESPONSES)
    elif intent_name == "thanks":
        response_text = random.choice(THANKS_RESPONSES)
    elif intent_name == "how_are_you":
        response_text = random.choice(HOW_ARE_YOU_RESPONSES)
    elif intent_name == "identity":
        response_text = random.choice(IDENTITY_RESPONSES)
    elif intent_name == "help":
        response_text = HELP_RESPONSE
    elif intent_name == "show_quick_replies":
        response_text = build_deterministic_response(normalized, intent_data, [])
    elif intent_name in ["categories", "stats"]:
        response_text = build_deterministic_response(normalized, intent_data, products)
    else:
        # Product queries & general shopping dialogue: Use RAG with Ollama
        response_text = generate_grounded_response(
            message=normalized,
            intent=intent_data,
            products=products,
            chat_history=messages,
            user=user,
        )

    # Step 4: Update User Preferences
    update_user_preferences(user, normalized, products)

    # Step 5: Suggestions (Embed Product Cards)
    suggestions = products[:5]

    # If no search matches, append personalized recommendations
    if not suggestions and intent_name == "product_search":
        personalized = get_personalized_recommendations(user, limit=3)
        if personalized:
            suggestions = personalized

    # Step 6: Dynamic Context-Aware Quick Replies
    quick_replies = get_quick_replies(
        intent=intent_name,
        products=suggestions,
        entities=entities,
        last_response=response_text,
    )

    payload = {
        "response": response_text,
        "suggestions": suggestions,
        "quick_replies": quick_replies,
    }

    persisted_state = {
        "messages": messages + [{"role": "assistant", "content": response_text}],
        "last_intent": intent_name,
        "last_query": normalized,
        "entities": entities,
    }

    # Step 7: Record Chat History
    if user and user.is_authenticated:
        ChatHistory.objects.create(
            user=user,
            message=normalized,
            response=response_text,
            context_used={
                "intent": intent_name,
                "confidence": intent_data.get("confidence", 0.8),
                "entities": entities,
                "suggestions_count": len(suggestions),
            },
        )

    # Cache for short TTL
    cache.set(cache_key, payload, CACHE_TTL_SECONDS)

    return payload, persisted_state