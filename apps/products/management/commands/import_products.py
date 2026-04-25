import pandas as pd
import requests
import os
import random
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from apps.products.models import Product, ProductImage, Category
from apps.companies.models import Company

class Command(BaseCommand):
    help = 'Products ko fast aur unique images ke saath import karein'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **options):
        User = get_user_model()
        file_path = options['file_path']
        
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("× Error: Superadmin nahi mila!"))
            return

        try:
            ext = os.path.splitext(file_path)[1].lower()
            df = pd.read_csv(file_path) if ext == '.csv' else pd.read_excel(file_path)
            
            total = len(df)
            self.stdout.write(self.style.SUCCESS(f'Total: {total}. Starting Fast Import...'))

            target_company, _ = Company.objects.get_or_create(
                name='c', 
                defaults={'user': admin_user}
            )

            for index, row in df.iterrows():
                try:
                    # 1. Category Setup
                    cat_name = str(row['category']).strip()
                    category, _ = Category.objects.get_or_create(name=cat_name)

                    # 2. Product Create/Update
                    product, created = Product.objects.update_or_create(
                        sku=row['sku'],
                        defaults={
                            'name': row['name'],
                            'category': category,
                            'company': target_company,
                            'description': row['description'],
                            'price': row['price'],
                            'stock_quantity': row['stock_quantity'],
                            'is_active': True,
                        }
                    )

                    # 3. FAST Image Logic (Unsplash Fix)
                    status_msg = "No Image"
                    if not product.images.exists():
                        # Agar Unsplash 503 de raha hai, toh Picsum use karein (Bohat Fast hai)
                        # SKU use karne se har product ki image unique rahegi
                        fast_url = f"https://picsum.photos/seed/{product.sku}/600/600"
                        
                        try:
                            headers = {'User-Agent': 'Mozilla/5.0'}
                            res = requests.get(fast_url, headers=headers, timeout=5)
                            
                            if res.status_code == 200:
                                img_obj = ProductImage(product=product, is_main=True)
                                img_obj.image.save(f"{product.slug}.jpg", ContentFile(res.content), save=True)
                                status_msg = "Image Saved ✔"
                            else:
                                status_msg = f"Failed (Status: {res.status_code})"
                        except Exception:
                            status_msg = "Timeout ⚠"

                    # Live Progress Update
                    self.stdout.write(f"[{index+1}/{total}] {product.name} ... {status_msg}")

                except Exception as row_err:
                    self.stdout.write(self.style.ERROR(f"Row {index} skipped: {row_err}"))

            self.stdout.write(self.style.SUCCESS('\n--- IMPORT SUCCESSFUL! ---'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Critical Error: {e}'))