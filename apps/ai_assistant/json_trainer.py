# apps/ai_assistant/json_trainer.py

import json
import os
import random
from typing import Dict, List, Any
from django.conf import settings

class JSONTrainer:
    """Train AI model using JSON data"""
    
    def __init__(self, json_file='ai_training_data.json'):
        self.json_file = json_file
        self.data = None
        self.category_map = {}
        self.products_by_category = {}
        self.all_products = []
        self.load_data()
        self.build_index()
    
    def load_data(self):
        """Load JSON data"""
        json_path = os.path.join(settings.BASE_DIR, self.json_file)
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ Loaded {len(self.data.get('products', []))} products from {self.json_file}")
        else:
            print(f"❌ File {self.json_file} not found!")
    
    def build_index(self):
        """Build search index from data"""
        if not self.data:
            return
        
        self.all_products = self.data.get('products', [])
        self.category_map = self.data.get('category_mapping', {})
        
        # Build category index
        self.products_by_category = {}
        for product in self.all_products:
            category = product.get('category_name', 'Uncategorized')
            if category not in self.products_by_category:
                self.products_by_category[category] = []
            self.products_by_category[category].append(product)
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Intelligent search with ranking"""
        if not query or not self.all_products:
            return []
        
        query_lower = query.lower().strip()
        results = []
        
        # Score each product
        for product in self.all_products:
            score = 0
            name = product.get('name', '').lower()
            category = product.get('category_name', '').lower()
            description = product.get('short_description', '').lower()
            
            # Exact match gets highest score
            if query_lower == name:
                score += 100
            elif query_lower in name:
                score += 50
            
            # Word matching
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 2:
                    if word in name:
                        score += 10
                    if word in category:
                        score += 8
                    if word in description:
                        score += 5
            
            # Category bonus
            if any(word in category for word in query_words):
                score += 15
            
            # Featured bonus
            if product.get('is_featured', False):
                score += 5
            
            # Sales bonus
            score += product.get('total_sold', 0) * 0.1
            
            if score > 0:
                results.append((product, score))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        return [p for p, _ in results[:limit]]
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """Get products by category"""
        if not category:
            return []
        
        category_lower = category.lower().strip()
        
        # Try exact match first
        for cat_name, products in self.products_by_category.items():
            if cat_name.lower() == category_lower:
                return products[:10]
        
        # Try partial match
        for cat_name, products in self.products_by_category.items():
            if category_lower in cat_name.lower() or cat_name.lower() in category_lower:
                return products[:10]
        
        return []
    
    def get_trending(self, limit: int = 5) -> List[Dict]:
        """Get trending products"""
        if not self.all_products:
            return []
        
        sorted_products = sorted(
            self.all_products,
            key=lambda x: x.get('total_sold', 0),
            reverse=True
        )
        return sorted_products[:limit]
    
    def get_featured(self, limit: int = 5) -> List[Dict]:
        """Get featured products"""
        featured = [p for p in self.all_products if p.get('is_featured', False)]
        return featured[:limit]
    
    def get_stats(self) -> Dict:
        """Get website statistics"""
        return {
            "total_products": len(self.all_products),
            "total_categories": len(self.products_by_category),
            "categories": list(self.products_by_category.keys())
        }
    
    def get_random_products(self, limit: int = 3) -> List[Dict]:
        """Get random products for fallback"""
        if not self.all_products:
            return []
        return random.sample(self.all_products, min(limit, len(self.all_products)))


# Singleton instance
trainer = JSONTrainer()