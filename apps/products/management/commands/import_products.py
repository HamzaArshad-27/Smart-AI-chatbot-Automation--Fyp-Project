import csv
import os
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.products.models import Product, Category
from apps.companies.models import Company

class Command(BaseCommand):
    help = 'Imports 100 products and links them to Company: Farhan'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        file_path = options['csv_file']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        # Fetch your existing company "Farhan"
        company = Company.objects.filter(name="Farhan").first()

        if not company:
            # Fallback if name changed: just get the first available company
            company = Company.objects.first()

        if not company:
            self.stdout.write(self.style.ERROR("❌ Error: No Company found in database."))
            return

        self.stdout.write(self.style.SUCCESS(f"Linking products to Company: {company.name} (ID: {company.id})"))

        with open(file_path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    # 1. Handle Category (Create if it doesn't exist)
                    category_name = row['category'].strip()
                    category_obj, _ = Category.objects.get_or_create(
                        name=category_name,
                        defaults={'slug': slugify(category_name)}
                    )

                    # 2. Create or Update Product based on SKU
                    product, created = Product.objects.update_or_create(
                        sku=row['sku'].strip(),
                        defaults={
                            'name': row['name'],
                            'category': category_obj,
                            'company': company,
                            'description': row['description'],
                            'short_description': row['short_description'],
                            'price': row['price'],
                            'compare_price': row['compare_price'] if row['compare_price'] else None,
                            'cost_per_item': row['cost_per_item'] if row['cost_per_item'] else 0,
                            'stock_quantity': row['stock_quantity'],
                            'barcode': row['barcode'],
                            'weight': row['weight'] if row['weight'] and row['weight'] != '' else 0,
                            'dimensions': row['dimensions'],
                            'is_active': str(row['is_active']).upper() == 'TRUE',
                            'is_featured': str(row['is_featured']).upper() == 'TRUE',
                            'is_digital': str(row['is_digital']).upper() == 'TRUE',
                            'slug': slugify(f"{row['name']}-{row['sku']}")
                        }
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f"✅ {'Created' if created else 'Updated'}: {product.name}"))
                    count += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error with {row.get('name')}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone! Successfully processed {count} products."))