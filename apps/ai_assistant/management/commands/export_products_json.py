# apps/products/management/commands/export_products_json.py

import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from apps.products.models import Product, Category
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Export products, categories, and users to JSON for AI training'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Starting database export...'))
        
        # 1. Export Categories
        self.stdout.write('📂 Exporting categories...')
        categories = Category.objects.filter(is_active=True)
        categories_data = []
        for c in categories:
            categories_data.append({
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "description": c.description or "",
                "is_active": c.is_active,
                "product_count": Product.objects.filter(category=c, is_active=True).count(),
                "created_at": c.created_at.isoformat() if hasattr(c, 'created_at') else None,
            })
        
        # 2. Export Products
        self.stdout.write('📦 Exporting products...')
        products = Product.objects.filter(is_active=True)
        products_data = []
        for p in products:
            products_data.append({
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "price": float(p.price),
                "category_id": p.category.id if p.category else None,
                "category_name": p.category.name if p.category else "",
                "description": p.description or "",
                "short_description": p.short_description or "",
                "is_featured": p.is_featured,
                "is_active": p.is_active,
                "total_sold": p.total_sold or 0,
                "average_rating": float(p.average_rating or 0),
                "stock": p.stock if hasattr(p, 'stock') else 0,
                "created_at": p.created_at.isoformat() if hasattr(p, 'created_at') else None,
                "url": f"/products/detail/{p.slug}/",
                "image_url": p.image.url if hasattr(p, 'image') and p.image else "",
            })
        
        # 3. Export Users (optional - for personalization)
        self.stdout.write('👤 Exporting users...')
        users = User.objects.all()[:100]  # Limit to 100 users
        users_data = []
        for u in users:
            users_data.append({
                "id": u.id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "is_active": u.is_active,
                "date_joined": u.date_joined.isoformat() if hasattr(u, 'date_joined') else None,
                "role": getattr(u, 'role', 'customer'),
            })
        
        # 4. Create website statistics
        self.stdout.write('📊 Creating statistics...')
        stats = {
            "total_products": Product.objects.filter(is_active=True).count(),
            "total_categories": Category.objects.filter(is_active=True).count(),
            "total_users": User.objects.count(),
            "featured_products": Product.objects.filter(is_active=True, is_featured=True).count(),
            "exported_at": datetime.now().isoformat(),
        }
        
        # 5. Combine all data
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "statistics": stats,
            "categories": categories_data,
            "products": products_data,
            "users": users_data,
            "category_mapping": {c["id"]: c["name"] for c in categories_data},
        }
        
        # 6. Save to file
        filename = "ai_training_data.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Export complete!'))
        self.stdout.write(f'📁 File saved as: {filename}')
        self.stdout.write(f'📊 Statistics:')
        self.stdout.write(f'   - Categories: {stats["total_categories"]}')
        self.stdout.write(f'   - Products: {stats["total_products"]}')
        self.stdout.write(f'   - Users: {stats["total_users"]}')
        self.stdout.write(f'   - Featured: {stats["featured_products"]}')