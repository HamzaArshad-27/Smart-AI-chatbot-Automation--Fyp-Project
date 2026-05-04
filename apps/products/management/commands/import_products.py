import pandas as pd
import requests
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from apps.products.models import Product, ProductImage, Category
from apps.companies.models import Company
import time

class Command(BaseCommand):
    help = 'Import products with unique images for a specific company'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **options):
        User = get_user_model()
        file_path = options['file_path']
        
        # Target user based on email
        target_email = "2231046@ncbae.edu.pk"
        owner_user = User.objects.filter(email=target_email).first()
        
        if not owner_user:
            self.stdout.write(self.style.ERROR(f"× Error: User with email {target_email} not found!"))
            return

        try:
            ext = os.path.splitext(file_path)[1].lower()
            df = pd.read_csv(file_path) if ext == '.csv' else pd.read_excel(file_path)
            
            total = len(df)
            self.stdout.write(self.style.SUCCESS(f'Total: {total}. Starting Fast Import...'))

            # Ensure the company exists for this specific user
            target_company, _ = Company.objects.get_or_create(
                user=owner_user,
                defaults={'name': 'Main Company'} # Change name as needed
            )

            for index, row in df.iterrows():
                try:
                    # 1. Category Setup - Ensure Category is Active
                    cat_name = str(row['category']).strip()
                    category, _ = Category.objects.get_or_create(
                        name=cat_name,
                        defaults={'is_active': True} 
                    )
                    
                    # Force active if category already existed but was inactive
                    if not category.is_active:
                        category.is_active = True
                        category.save()

                    # 2. Product Create/Update - Set is_active to True
                    product, created = Product.objects.update_or_create(
                        sku=row['sku'],
                        defaults={
                            'name': row['name'],
                            'category': category,
                            'company': target_company,
                            'description': row['description'],
                            'price': row['price'],
                            'stock_quantity': row['stock_quantity'],
                            'is_active': True, # Ensures product is active
                        }
                    )

# ... (Previous imports remain the same)

# 3. RELEVANT Image Logic with Fallback
# ... inside the loop
                    # 3. STABLE RELEVANT Image Logic
                    status_msg = "Image Exists"
                    if not product.images.exists():
                        # We use a keyword-based search via a reliable placeholder or a different source
                        # Replacing spaces with hyphens often helps these scrapers/APIs
                        keyword = product.name.split(' ')[0].lower() # Gets the first word (e.g., 'Tennis')
                        
                        # New Strategy: Use a more stable endpoint or a better formatted query
                        # If Unsplash is failing, we can try this specific format which is sometimes more resilient
                        stable_url = f"https://loremflickr.com/600/600/{keyword}"
                        
                        try:
                            headers = {'User-Agent': 'Mozilla/5.0'}
                            res = requests.get(stable_url, headers=headers, timeout=10)
                            
                            if res.status_code == 200:
                                img_obj = ProductImage(product=product, is_main=True)
                                img_obj.image.save(f"{product.sku}.jpg", ContentFile(res.content), save=True)
                                status_msg = f"Relevant Image ({keyword}) Saved ✔"
                            else:
                                # Final Fallback to Picsum if even Flickr fails
                                fallback_url = f"https://picsum.photos/seed/{product.sku}/600/600"
                                res = requests.get(fallback_url, headers=headers, timeout=5)
                                img_obj = ProductImage(product=product, is_main=True)
                                img_obj.image.save(f"{product.sku}.jpg", ContentFile(res.content), save=True)
                                status_msg = "Generic Fallback Saved ⚠"
                                
                        except Exception:
                            status_msg = "Timeout ⚠"

                    # Crucial: Keep this sleep to avoid being blocked!
                    time.sleep(1.0)

                    self.stdout.write(f"[{index+1}/{total}] {product.name} ... {status_msg}")


                except Exception as row_err:
                    self.stdout.write(self.style.ERROR(f"Row {index} skipped: {row_err}"))

            self.stdout.write(self.style.SUCCESS('\n--- IMPORT SUCCESSFUL! ---'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Critical Error: {e}'))