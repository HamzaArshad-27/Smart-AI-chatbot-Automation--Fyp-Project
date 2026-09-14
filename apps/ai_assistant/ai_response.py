# apps/ai_assistant/ai_response.py

import json
import random
from apps.ai_assistant.json_trainer import trainer
from typing import Dict

class AIResponseGenerator:
    """Generate natural AI responses using trained data"""
    
    @staticmethod
    def get_categories_response() -> str:
        """Response for categories query"""
        stats = trainer.get_stats()
        categories = stats.get('categories', [])
        
        if categories:
            cat_list = ", ".join(categories[:10])
            return f"📂 We have these categories in our store:\n\n{cat_list}\n\nWhich category are you interested in?"
        return "We have various categories including Electronics, Clothing, and more!"
    
    @staticmethod
    def get_stats_response() -> str:
        """Response for stats query"""
        stats = trainer.get_stats()
        return f"📊 Welcome to Vendora!\n\nWe have {stats['total_products']} products in {stats['total_categories']} categories.\n\nHow can I help you today?"
    
    @staticmethod
    def get_trending_response() -> str:
        """Response for trending products"""
        trending = trainer.get_trending(5)
        if trending:
            product_list = "\n".join([
                f"• {p['name']} - ${p['price']} {p.get('url', '')}"
                for p in trending[:5]
            ])
            return f"🔥 Our trending products right now:\n\n{product_list}\n\nWould you like more details about any of these?"
        return "I couldn't find any trending products right now. Check our homepage for featured items!"
    
    @staticmethod
    def get_featured_response() -> str:
        """Response for featured products"""
        featured = trainer.get_featured(5)
        if featured:
            product_list = "\n".join([
                f"• {p['name']} - ${p['price']} {p.get('url', '')}"
                for p in featured[:5]
            ])
            return f"⭐ Our featured products:\n\n{product_list}\n\nWould you like to see more?"
        return "We have many great products! Which category interests you?"
    
    @staticmethod
    def get_search_response(query: str) -> Dict:
        """Response for product search"""
        if not query:
            return {
                "response": "Please tell me what you're looking for!",
                "products": []
            }
        
        results = trainer.search(query, 5)
        
        if results:
            product_list = "\n".join([
                f"• {p['name']} - ${p['price']} {p.get('url', '')}"
                for p in results[:5]
            ])
            return {
                "response": f"🔍 Here are products matching '{query}':\n\n{product_list}\n\nClick on any product to view details.",
                "products": results
            }
        else:
            return {
                "response": f"I couldn't find any products matching '{query}'. 😕\n\nTry:\n• Using different keywords\n• Checking categories\n• Viewing trending products",
                "products": []
            }
    
    @staticmethod
    def get_category_response(category: str) -> Dict:
        """Response for category products"""
        if not category:
            return {
                "response": "Please tell me which category you're interested in!",
                "products": []
            }
        
        products = trainer.get_products_by_category(category)
        
        if products:
            product_list = "\n".join([
                f"• {p['name']} - ${p['price']} {p.get('url', '')}"
                for p in products[:5]
            ])
            return {
                "response": f"📂 Here are products in {category}:\n\n{product_list}\n\nWould you like more details?",
                "products": products
            }
        else:
            categories = trainer.get_stats().get('categories', [])
            return {
                "response": f"I couldn't find products in '{category}'. Available categories: {', '.join(categories[:5])}",
                "products": []
            }
    
    @staticmethod
    def get_chitchat_response(message: str) -> str:
        """Natural chitchat responses"""
        msg = message.lower().strip()
        
        responses = {
            "hello": [
                "Hello! 👋 How can I help you shop today?",
                "Hi there! Welcome to Vendora. What brings you here?",
                "Hey! Looking for something special today?"
            ],
            "how_are_you": [
                "I'm doing great, thanks for asking! 😊 What products are you looking for?",
                "I'm fantastic! Always happy to help shoppers. What can I assist you with?"
            ],
            "name": [
                "I'm Vendora AI, your personal shopping assistant! 🤖",
                "You can call me Vendora! I'm your AI shopping guide."
            ],
            "what_can_you_do": [
                "I can help you find products, show you categories, and recommend trending items! 🛍️\n\nTry asking:\n• 'show me laptops'\n• 'what are your categories'\n• 'trending products'"
            ],
            "thank_you": [
                "You're welcome! 😊 Is there anything else I can help with?",
                "Happy to help! Let me know if you need anything else!"
            ],
            "bye": [
                "Goodbye! Come back anytime! 👋",
                "Bye! Have a great day and happy shopping! 🛍️"
            ],
            "urdu": [
                "Aap Urdu mein pooch sakte hain! 😊\n\nExamples:\n• 'mujhe laptop chahiye'\n• 'categories dikhao'\n• 'trending products kya hain'"
            ]
        }
        
        # Urdu detection
        if any(ord(c) >= 0x0600 and ord(c) <= 0x06FF for c in msg if c):
            return random.choice(responses["urdu"])
        
        # English responses
        if "hello" in msg or "hi" in msg or "hey" in msg:
            return random.choice(responses["hello"])
        if any(w in msg for w in ["how are you", "how r u", "how's it going"]):
            return random.choice(responses["how_are_you"])
        if any(w in msg for w in ["what is your name", "who are you"]):
            return random.choice(responses["name"])
        if any(w in msg for w in ["what can you do", "help me"]):
            return random.choice(responses["what_can_you_do"])
        if any(w in msg for w in ["thanks", "thank you"]):
            return random.choice(responses["thank_you"])
        if any(w in msg for w in ["bye", "goodbye", "see you"]):
            return random.choice(responses["bye"])
        
        return random.choice(responses["hello"])


# Singleton instance
ai_response = AIResponseGenerator()