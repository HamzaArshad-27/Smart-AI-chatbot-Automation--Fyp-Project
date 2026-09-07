import json
import logging
from typing import Dict, Any, List
from django.core.cache import cache
from django.db.models import Q
from apps.products.models import Product, Category
from apps.ai_assistant.data_loader import WebsiteDataLoader
from apps.ai_assistant.services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class AIAgent:
    """True AI Agent with database access and natural conversation"""
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.context = {}
        
    def process_query(self, user_message: str, user=None, chat_history=None) -> Dict[str, Any]:
        """Process user query with full AI capabilities"""
        
        # Step 1: Analyze the query
        analysis = self._analyze_query(user_message, chat_history)
        
        # Step 2: Fetch relevant data from database
        data = self._fetch_data(analysis)
        
        # Step 3: Generate intelligent response
        response = self._generate_response(user_message, analysis, data, chat_history)
        
        return response
    
    def _analyze_query(self, message: str, history=None) -> Dict[str, Any]:
        """Analyze user query to understand intent and extract entities"""
        
        prompt = f"""Analyze this user message for an e-commerce assistant.
        
User message: {message}

Return JSON with:
1. intent: (product_search, category_browse, general_question, chitchat, recommendation, comparison, help)
2. entities: (products, categories, brands, price_range, features mentioned)
3. sentiment: (positive, negative, neutral)
4. complexity: (simple, moderate, complex)
5. requires_database: (true/false)

JSON:"""
        
        try:
            raw = self.ollama.classify_with_prompt(prompt)
            return json.loads(raw) if isinstance(raw, str) else raw
        except:
            # Fallback analysis
            return self._fallback_analysis(message)
    
    def _fallback_analysis(self, message: str) -> Dict[str, Any]:
        """Fallback if Ollama fails"""
        msg = message.lower()
        
        # Detect intent
        if any(w in msg for w in ["how many", "total", "count"]):
            intent = "general_question"
        elif any(w in msg for w in ["compare", "vs", "difference"]):
            intent = "comparison"
        elif any(w in msg for w in ["recommend", "suggest", "best"]):
            intent = "recommendation"
        elif any(w in msg for w in ["category", "list", "browse"]):
            intent = "category_browse"
        elif any(w in msg for w in ["hello", "hi", "hey", "how are"]):
            intent = "chitchat"
        elif any(w in msg for w in ["help", "what can you do"]):
            intent = "help"
        else:
            intent = "product_search"
        
        return {
            "intent": intent,
            "entities": {"products": [msg]},
            "sentiment": "neutral",
            "complexity": "simple",
            "requires_database": True
        }
    
    def _fetch_data(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch relevant data from database based on analysis"""
        
        data = {
            "products": [],
            "categories": [],
            "stats": {},
            "trending": []
        }
        
        intent = analysis.get("intent", "")
        entities = analysis.get("entities", {})
        
        # Get all categories
        categories = WebsiteDataLoader.get_categories_for_ai()
        data["categories"] = categories[:10]
        
        # Get stats
        stats = cache.get("ai_data_stats")
        if not stats:
            stats = WebsiteDataLoader.load_website_stats()
        data["stats"] = stats
        
        # Get trending products
        trending = WebsiteDataLoader.get_trending_for_ai()
        data["trending"] = trending[:5]
        
        # Product search
        if intent in ["product_search", "recommendation", "comparison"]:
            search_terms = entities.get("products", [])
            if search_terms:
                for term in search_terms:
                    products = WebsiteDataLoader.get_products_for_ai(term)
                    data["products"].extend(products[:5])
            else:
                # Get featured products
                products = Product.objects.filter(is_active=True, is_featured=True)[:5]
                data["products"] = WebsiteDataLoader.load_products()[:5]
        
        # Category browse
        if intent == "category_browse":
            category_name = entities.get("categories", [""])[0] if entities.get("categories") else ""
            if category_name:
                products = Product.objects.filter(
                    Q(category__name__icontains=category_name) |
                    Q(category__slug__icontains=category_name)
                ).filter(is_active=True)[:5]
                if products:
                    data["products"] = [
                        {
                            "id": p.id,
                            "name": p.name,
                            "price": str(p.price),
                            "url": f"/products/{p.slug}/"
                        }
                        for p in products
                    ]
        
        return data
    
    def _generate_response(self, message: str, analysis: Dict, data: Dict, history=None) -> Dict[str, Any]:
        """Generate intelligent response using Ollama"""
        
        intent = analysis.get("intent", "general")
        
        # Build context for Ollama
        context = self._build_context(message, analysis, data, history)
        
        # Generate response
        try:
            result = self.ollama.generate_conversation_json(
                user_message=message,
                chat_history=history or [],
                runtime_context=context
            )
            
            response_text = result.get("reply", "")
            product_ids = result.get("product_ids", [])
            
            # If no products in response but we have data, add them
            if not product_ids and data.get("products"):
                product_ids = [p.get("id") for p in data["products"][:5] if p.get("id")]
                
                # Add product info to response
                if data["products"]:
                    product_list = "\n".join([
                        f"• {p['name']} - ${p['price']}"
                        for p in data["products"][:5]
                    ])
                    response_text = f"{response_text}\n\nHere are some options:\n{product_list}"
            
            return {
                "response": response_text,
                "suggestions": data["products"][:5],
                "intent": intent,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return self._fallback_response(message, data)
    
    def _build_context(self, message: str, analysis: Dict, data: Dict, history) -> str:
        """Build rich context for Ollama"""
        
        context_parts = []
        
        # Add website stats
        stats = data.get("stats", {})
        context_parts.append(f"Website Stats:")
        context_parts.append(f"- Total Products: {stats.get('total_products', 0)}")
        context_parts.append(f"- Total Categories: {stats.get('total_categories', 0)}")
        context_parts.append(f"- Featured Products: {stats.get('featured_products', 0)}")
        
        # Add categories
        categories = data.get("categories", [])
        if categories:
            context_parts.append(f"\nAvailable Categories: {', '.join([c['name'] for c in categories[:10]])}")
        
        # Add products
        products = data.get("products", [])
        if products:
            context_parts.append(f"\nFound Products ({len(products)}):")
            for p in products[:5]:
                context_parts.append(f"- {p.get('name')} (${p.get('price', '0')})")
        
        # Add trending
        trending = data.get("trending", [])
        if trending:
            context_parts.append(f"\nTrending Products: {', '.join([p['name'] for p in trending[:3]])}")
        
        # Add analysis context
        context_parts.append(f"\nIntent: {analysis.get('intent', 'unknown')}")
        context_parts.append(f"Sentiment: {analysis.get('sentiment', 'neutral')}")
        context_parts.append(f"Complexity: {analysis.get('complexity', 'simple')}")
        
        return "\n".join(context_parts)
    
    def _fallback_response(self, message: str, data: Dict) -> Dict[str, Any]:
        """Fallback if Ollama fails"""
        
        products = data.get("products", [])
        
        if products:
            product_list = "\n".join([
                f"• {p['name']} - ${p['price']}"
                for p in products[:5]
            ])
            return {
                "response": f"I found these products for you:\n{product_list}\n\nWould you like more details about any of them?",
                "suggestions": products[:5],
                "intent": "product_search",
                "analysis": {}
            }
        
        stats = data.get("stats", {})
        return {
            "response": f"I have {stats.get('total_products', 0)} products in {stats.get('total_categories', 0)} categories. What would you like to know more about?",
            "suggestions": [],
            "intent": "general",
            "analysis": {}
        }


# Singleton instance
ai_agent = AIAgent()