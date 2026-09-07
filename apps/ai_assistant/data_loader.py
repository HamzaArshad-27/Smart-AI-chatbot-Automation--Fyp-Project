import json
import logging
from datetime import datetime
from django.core.cache import cache
from django.db.models import Count, Avg
from apps.products.models import Product, Category

logger = logging.getLogger(__name__)

# Cache keys
CACHE_KEY_PRODUCTS = "ai_data_products"
CACHE_KEY_CATEGORIES = "ai_data_categories"
CACHE_KEY_TRENDING = "ai_data_trending"
CACHE_KEY_STATS = "ai_data_stats"
CACHE_TTL = 3600  # 1 hour

class WebsiteDataLoader:
    """Load and cache all website data for AI assistant"""
    
    @staticmethod
    def load_all_data():
        """Load all data from database"""
        try:
            data = {
                "products": WebsiteDataLoader.load_products(),
                "categories": WebsiteDataLoader.load_categories(),
                "trending": WebsiteDataLoader.load_trending_products(),
                "stats": WebsiteDataLoader.load_website_stats(),
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache all data
            cache.set(CACHE_KEY_PRODUCTS, data["products"], CACHE_TTL)
            cache.set(CACHE_KEY_CATEGORIES, data["categories"], CACHE_TTL)
            cache.set(CACHE_KEY_TRENDING, data["trending"], CACHE_TTL)
            cache.set(CACHE_KEY_STATS, data["stats"], CACHE_TTL)
            
            logger.info(f"✅ AI Data loaded: {len(data['products'])} products, {len(data['categories'])} categories")
            return data
        except Exception as e:
            logger.error(f"❌ Error loading AI data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def load_products(limit=100):
        """Load all active products with details"""
        try:
            products = Product.objects.filter(is_active=True).order_by('-created_at')[:limit]
            result = []
            for p in products:
                product_data = {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "price": str(p.price),
                    "category": p.category.name if p.category else "",
                    "description": p.short_description or (p.description[:200] if p.description else ""),
                    "is_featured": p.is_featured,
                    "total_sold": p.total_sold or 0,
                    "average_rating": float(p.average_rating or 0),
                    "url": f"/products/{p.slug}/"
                }
                # Add image only if field exists
                if hasattr(p, 'image') and p.image:
                    product_data["image_url"] = p.image.url if hasattr(p.image, 'url') else ""
                result.append(product_data)
            return result
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            return []
    
    @staticmethod
    def load_categories():
        """Load all categories"""
        try:
            categories = Category.objects.filter(is_active=True)
            result = []
            for c in categories:
                category_data = {
                    "id": c.id,
                    "name": c.name,
                    "slug": c.slug,
                    "description": c.description or "",
                    "product_count": c.products.count() if hasattr(c, 'products') else 0,  # FIXED
                }
                if hasattr(c, 'image') and c.image:
                    category_data["image_url"] = c.image.url if hasattr(c.image, 'url') else ""
                result.append(category_data)
            return result
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            return []
    
    @staticmethod
    def load_trending_products(limit=10):
        """Load trending/popular products"""
        try:
            products = Product.objects.filter(is_active=True).order_by('-total_sold', '-average_rating')[:limit]
            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": str(p.price),
                    "total_sold": p.total_sold or 0,
                    "average_rating": float(p.average_rating or 0),
                    "url": f"/products/{p.slug}/"
                }
                for p in products
            ]
        except Exception as e:
            logger.error(f"Error loading trending products: {e}")
            return []
    
    @staticmethod
    def load_website_stats():
        """Load website statistics"""
        try:
            return {
                "total_products": Product.objects.filter(is_active=True).count(),
                "total_categories": Category.objects.filter(is_active=True).count(),
                "featured_products": Product.objects.filter(is_active=True, is_featured=True).count(),
                "total_orders": 0,  # Add if orders app exists
                "total_users": 0,  # Add if user model is accessible
            }
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
            return {
                "total_products": 0,
                "total_categories": 0,
                "featured_products": 0,
                "total_orders": 0,
                "total_users": 0,
            }

    @staticmethod
    def get_products_for_ai(query=""):
        """Get products for AI responses with filtering"""
        cached = cache.get(CACHE_KEY_PRODUCTS)
        if not cached:
            cached = WebsiteDataLoader.load_products()
        
        if query:
            query_lower = query.lower()
            # Search in products
            return [
                p for p in cached 
                if query_lower in p['name'].lower() 
                or query_lower in p['category'].lower() 
                or query_lower in (p.get('description') or '').lower()
            ][:10]
        return cached
    
    @staticmethod
    def get_categories_for_ai():
        """Get categories for AI responses"""
        cached = cache.get(CACHE_KEY_CATEGORIES)
        if not cached:
            cached = WebsiteDataLoader.load_categories()
        return cached
    
    @staticmethod
    def get_trending_for_ai():
        """Get trending products for AI responses"""
        cached = cache.get(CACHE_KEY_TRENDING)
        if not cached:
            cached = WebsiteDataLoader.load_trending_products()
        return cached


def refresh_ai_data():
    """Refresh AI data cache"""
    WebsiteDataLoader.load_all_data()
    logger.info("🔄 AI data cache refreshed")