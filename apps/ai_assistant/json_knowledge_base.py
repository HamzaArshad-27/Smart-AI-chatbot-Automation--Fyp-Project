# apps/ai_assistant/json_knowledge_base.py

import json
import os
from typing import Dict, List, Any, Optional
from django.conf import settings

class JSONKnowledgeBase:
    """Load and query JSON training data from exported database"""
    
    def __init__(self, json_file='ai_training_data.json'):
        self.json_file = json_file
        self.data = None
        self.load_data()
    
    def load_data(self):
        """Load JSON data from file"""
        json_path = os.path.join(settings.BASE_DIR, self.json_file)
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ Loaded {len(self.data.get('products', []))} products from {self.json_file}")
            return self.data
        else:
            print(f"❌ File {self.json_file} not found!")
            print("💡 Run: python manage.py export_products_json")
            return None
    
    def get_all_products(self) -> List[Dict]:
        """Get all products"""
        return self.data.get('products', []) if self.data else []
    
    def get_all_categories(self) -> List[Dict]:
        """Get all categories"""
        return self.data.get('categories', []) if self.data else []
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """Search products by name, category, or description"""
        if not self.data:
            return []
        
        query = query.lower()
        results = []
        
        for product in self.data.get('products', []):
            # Search in name, category, and description
            if (query in product['name'].lower() or 
                query in product.get('category_name', '').lower() or
                query in product.get('short_description', '').lower() or
                query in product.get('description', '').lower()):
                results.append(product)
        
        return results[:limit]
    
    def get_products_by_category(self, category_name: str) -> List[Dict]:
        """Get all products in a category"""
        if not self.data:
            return []
        
        category_name = category_name.lower()
        return [
            p for p in self.data.get('products', [])
            if category_name in p.get('category_name', '').lower()
        ]
    
    def get_products_by_category_id(self, category_id: int) -> List[Dict]:
        """Get all products in a category by ID"""
        if not self.data:
            return []
        
        return [
            p for p in self.data.get('products', [])
            if p.get('category_id') == category_id
        ]
    
    def get_trending_products(self, limit: int = 5) -> List[Dict]:
        """Get trending products by total_sold"""
        if not self.data:
            return []
        
        products = sorted(
            self.data.get('products', []),
            key=lambda x: x.get('total_sold', 0),
            reverse=True
        )
        return products[:limit]
    
    def get_featured_products(self, limit: int = 5) -> List[Dict]:
        """Get featured products"""
        if not self.data:
            return []
        
        products = [
            p for p in self.data.get('products', [])
            if p.get('is_featured', False)
        ]
        return products[:limit]
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get a product by ID"""
        if not self.data:
            return None
        
        for product in self.data.get('products', []):
            if product.get('id') == product_id:
                return product
        return None
    
    def get_category_by_id(self, category_id: int) -> Optional[Dict]:
        """Get a category by ID"""
        if not self.data:
            return None
        
        for category in self.data.get('categories', []):
            if category.get('id') == category_id:
                return category
        return None
    
    def get_statistics(self) -> Dict:
        """Get website statistics"""
        if not self.data:
            return {"total_products": 0, "total_categories": 0}
        
        return self.data.get('statistics', {})
    
    def get_all_category_names(self) -> List[str]:
        """Get all category names"""
        if not self.data:
            return []
        
        return [c['name'] for c in self.data.get('categories', [])]
    
    def get_products_by_price_range(self, min_price: float, max_price: float) -> List[Dict]:
        """Get products within a price range"""
        if not self.data:
            return []
        
        return [
            p for p in self.data.get('products', [])
            if min_price <= p.get('price', 0) <= max_price
        ]


# Create a singleton instance
knowledge_base = JSONKnowledgeBase()