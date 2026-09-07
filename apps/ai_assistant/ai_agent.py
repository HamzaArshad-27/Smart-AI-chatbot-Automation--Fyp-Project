# apps/ai_assistant/ai_agent.py
import json
import logging
from typing import Dict, Any, List, Optional
from django.core.cache import cache
from django.db.models import Q

from apps.products.models import Product, Category
from apps.ai_assistant.data_loader import WebsiteDataLoader
from apps.ai_assistant.services.ollama_client import OllamaClient
from apps.ai_assistant.services.product_retrieval import hybrid_search, serialize_product
from apps.ai_assistant.services.embedding_service import embedding_service
from apps.ai_assistant.entity_extractor import extract_entities, has_entities
from apps.ai_assistant.persona import VENDORA_PRODUCT_PROMPT, VENDORA_CLASSIFY_PROMPT
from apps.ai_assistant.verifier import verify_response, build_product_context

logger = logging.getLogger(__name__)


class AIAgent:
    """Intelligent Shopping Agent with Hybrid Retrieval, Entity Awareness, and Grounding."""

    def __init__(self):
        self.ollama = OllamaClient()
        self.context = {}

    def process_query(self, user_message: str, user=None, chat_history=None) -> Dict[str, Any]:
        """Process user query with full AI capabilities and grounded database retrieval."""
        # Step 1: Analyze the query (Ollama classification + Rule-based entity extraction)
        analysis = self._analyze_query(user_message, chat_history)

        # Step 2: Fetch relevant data using hybrid search & DB queries
        data = self._fetch_data(analysis, user=user)

        # Step 3: Generate grounded intelligent response
        response = self._generate_response(user_message, analysis, data, chat_history)

        return response

    def _analyze_query(self, message: str, history=None) -> Dict[str, Any]:
        """Analyze user query to understand intent and extract entities."""
        # Rule-based entities extraction as baseline or enrichment
        rule_entities = extract_entities(message)

        prompt = f"""{VENDORA_CLASSIFY_PROMPT}

User message: {message}

JSON:"""

        analysis = None
        try:
            raw = self.ollama.classify_with_prompt(prompt)
            if isinstance(raw, str):
                analysis = json.loads(raw)
            elif isinstance(raw, dict):
                analysis = raw
        except Exception as e:
            logger.debug(f"Ollama classify failed, using fallback: {e}")
            analysis = self._fallback_analysis(message)

        if not analysis or not isinstance(analysis, dict):
            analysis = self._fallback_analysis(message)

        # Merge rule entities into analysis entities
        entities = analysis.get("entities")
        if not isinstance(entities, dict):
            entities = {}

        # Merge extracted categories, brands, price
        merged_categories = list(set(entities.get("categories", []) + rule_entities.get("categories", [])))
        merged_brands = list(set(entities.get("brands", []) + rule_entities.get("brands", [])))
        
        entities["categories"] = merged_categories
        entities["brands"] = merged_brands
        entities["price_min"] = entities.get("price_min") or rule_entities.get("price_min")
        entities["price_max"] = entities.get("price_max") or rule_entities.get("price_max")
        entities["colors"] = rule_entities.get("colors", [])
        entities["sizes"] = rule_entities.get("sizes", [])
        entities["raw_query"] = rule_entities.get("raw_query", message)
        
        analysis["entities"] = entities
        return analysis

    def _fallback_analysis(self, message: str) -> Dict[str, Any]:
        """Fallback rule-based analysis if Ollama is unavailable."""
        msg = message.lower()
        rule_entities = extract_entities(message)

        if any(w in msg for w in ["how many", "total", "count", "store stats"]):
            intent = "general_question"
        elif any(w in msg for w in ["compare", "vs", "difference"]):
            intent = "comparison"
        elif any(w in msg for w in ["recommend", "suggest", "best", "trending", "featured"]):
            intent = "recommendation"
        elif any(w in msg for w in ["category", "categories", "sections", "browse"]):
            intent = "category_browse"
        elif any(w in msg for w in ["hello", "hi", "hey", "how are", "who are you"]):
            intent = "chitchat"
        elif any(w in msg for w in ["help", "what can you do"]):
            intent = "help"
        else:
            intent = "product_search"

        return {
            "intent": intent,
            "entities": rule_entities,
            "sentiment": "neutral",
            "complexity": "simple",
            "requires_database": True
        }

    def _fetch_data(self, analysis: Dict[str, Any], user=None) -> Dict[str, Any]:
        """Fetch relevant grounded data using hybrid search and DB loaders."""
        data = {
            "products": [],
            "categories": [],
            "stats": {},
            "trending": []
        }

        intent = analysis.get("intent", "")
        entities = analysis.get("entities", {})

        # Load categories
        categories = WebsiteDataLoader.get_categories_for_ai()
        data["categories"] = categories[:10]

        # Load stats
        stats = cache.get("ai_data_stats")
        if not stats:
            stats = WebsiteDataLoader.load_website_stats()
        data["stats"] = stats

        # Load trending products
        trending = WebsiteDataLoader.get_trending_for_ai()
        data["trending"] = trending[:5]

        # Product Search / Recommendation / Comparison
        if intent in ["product_search", "recommendation", "comparison", "general"]:
            search_query = entities.get("raw_query") or analysis.get("raw_query") or ""
            # Use hybrid search (FAISS + FTS + Entity filters + User interests)
            found_products = hybrid_search(
                query=search_query,
                entities=entities,
                user=user,
                limit=6
            )
            data["products"] = found_products

            # Fallback if no products found with query but entities exist
            if not data["products"] and entities.get("categories"):
                cat_name = entities["categories"][0]
                prods = Product.objects.filter(category__name__icontains=cat_name, is_active=True)[:5]
                data["products"] = [serialize_product(p) for p in prods]

            if not data["products"]:
                # Show featured or trending as fallback
                data["products"] = trending[:5]

        elif intent == "category_browse":
            category_names = entities.get("categories", [])
            if category_names:
                cat_name = category_names[0]
                prods = Product.objects.filter(
                    Q(category__name__icontains=cat_name) | Q(category__slug__icontains=cat_name),
                    is_active=True
                )[:6]
                data["products"] = [serialize_product(p) for p in prods]

        return data

    def _generate_response(self, message: str, analysis: Dict, data: Dict, history=None) -> Dict[str, Any]:
        """Generate grounded response using Ollama with fact verification."""
        intent = analysis.get("intent", "general")
        context = self._build_context(message, analysis, data, history)

        try:
            result = self.ollama.generate_with_context(
                system_prompt=VENDORA_PRODUCT_PROMPT,
                user_message=message,
                context=context,
                chat_history=history or [],
                temperature=0.3,
                max_tokens=180
            )

            raw_reply = result.get("reply", "")

            # Verify response against retrieved products to prevent hallucination
            verified_reply = verify_response(raw_reply, data.get("products", []))

            return {
                "response": verified_reply,
                "suggestions": data.get("products", [])[:5],
                "intent": intent,
                "analysis": analysis
            }

        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return self._fallback_response(message, data)

    def _build_context(self, message: str, analysis: Dict, data: Dict, history) -> str:
        """Build grounded context for Ollama."""
        context_parts = []

        # Website Stats
        stats = data.get("stats", {})
        context_parts.append(
            f"Website Stats: {stats.get('total_products', 0)} total products, {stats.get('total_categories', 0)} categories."
        )

        # Categories
        categories = data.get("categories", [])
        if categories:
            cat_names = ", ".join([c["name"] for c in categories[:8]])
            context_parts.append(f"Available Store Categories: {cat_names}")

        # Grounded Products List
        products = data.get("products", [])
        if products:
            context_parts.append(build_product_context(products[:6]))

        # Trending
        trending = data.get("trending", [])
        if trending:
            trend_str = ", ".join([f"{p['name']} (${p.get('price', '')})" for p in trending[:3]])
            context_parts.append(f"Popular Right Now: {trend_str}")

        return "\n\n".join(context_parts)

    def _fallback_response(self, message: str, data: Dict) -> Dict[str, Any]:
        """Fallback response if generation fails."""
        products = data.get("products", [])
        if products:
            product_list = "\n".join([f"• {p['name']} - ${p['price']}" for p in products[:5]])
            return {
                "response": f"I found these products for you:\n\n{product_list}\n\nWould you like more details about any of them?",
                "suggestions": products[:5],
                "intent": "product_search",
                "analysis": {}
            }

        stats = data.get("stats", {})
        return {
            "response": f"Welcome to Vendora! We have {stats.get('total_products', 0)} products across {stats.get('total_categories', 0)} categories. How can I assist your shopping today?",
            "suggestions": [],
            "intent": "general",
            "analysis": {}
        }


# Singleton instance
ai_agent = AIAgent()