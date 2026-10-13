
import csv
import io
import time
from decimal import Decimal
from pathlib import Path

import requests
from PIL import Image, UnidentifiedImageError

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.deletion import ProtectedError, RestrictedError

from apps.companies.models import Company
from apps.products.models import Product, ProductImage, Category


EMAIL = "moazjamil046@gmail.com"
COMPANY_ID = 1


class Command(BaseCommand):
    help = "Replace company products using the existing CSV and image URLs"

    def add_arguments(self, parser):
        parser.add_argument("file_path")
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Delete existing company products and import new products",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["file_path"])

        if not csv_path.is_file():
            raise CommandError("CSV file not found.")

        with csv_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            rows = list(csv.DictReader(file))

        required_columns = {
            "sku",
            "name",
            "category",
            "description",
            "price",
            "stock_quantity",
            "image_url",
        }

        if not rows:
            raise CommandError("CSV is empty.")

        missing_columns = required_columns - set(rows[0].keys())

        if missing_columns:
            raise CommandError(
                f"Missing columns: {missing_columns}"
            )

        if len(rows) != 200:
            raise CommandError(
                f"Expected 200 products, found {len(rows)}"
            )

        skus = [row["sku"].strip() for row in rows]

        if len(set(skus)) != 200 or any(not sku for sku in skus):
            raise CommandError("Duplicate or empty SKU found.")

        User = get_user_model()

        user = User.objects.filter(email=EMAIL).first()

        if not user:
            raise CommandError("Target user not found.")

        company = Company.objects.filter(
            id=COMPANY_ID,
            user=user,
        ).first()

        if not company:
            raise CommandError("Target company not found.")

        conflicting = Product.objects.filter(
            sku__in=skus
        ).exclude(company=company)

        if conflicting.exists():
            raise CommandError(
                "Some SKUs belong to another company."
            )

        existing_count = Product.objects.filter(
            company=company
        ).count()

        self.stdout.write(
            f"Company: {company.name}\n"
            f"Existing products: {existing_count}\n"
            f"CSV products: {len(rows)}"
        )

        if not options["commit"]:
            self.stdout.write(
                "DRY RUN: No database changes made.\n"
                "Use --commit to start image validation and import."
            )
            return

        # STEP 1: Download and validate ALL images first.
        # Existing products are not deleted if any image fails.
        self.stdout.write(
            "Downloading and validating 200 product images..."
        )

        downloaded_images = {}
        failures = []

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })

        for index, row in enumerate(rows, start=1):
            sku = row["sku"].strip()
            url = row["image_url"].strip()

            if not url.startswith(("https://", "http://")):
                failures.append(f"{sku}: invalid image URL")
                continue

            try:
                response = session.get(
                    url,
                    timeout=20,
                    allow_redirects=True,
                )
                response.raise_for_status()

                content = response.content

                with Image.open(io.BytesIO(content)) as img:
                    img.verify()

                with Image.open(io.BytesIO(content)) as img:
                    image_format = img.format

                extension = {
                    "JPEG": "jpg",
                    "PNG": "png",
                    "WEBP": "webp",
                }.get(image_format)

                if not extension:
                    raise ValueError(
                        f"Unsupported image format: {image_format}"
                    )

                downloaded_images[sku] = (
                    f"{sku}.{extension}",
                    content,
                )

                self.stdout.write(
                    f"[{index}/200] Image ready: {sku}"
                )

            except (
                requests.RequestException,
                UnidentifiedImageError,
                ValueError,
                OSError,
            ) as exc:
                failures.append(f"{sku}: {exc}")

            time.sleep(0.2)

        session.close()

        if failures:
            self.stderr.write(
                f"{len(failures)} images failed."
            )
            for failure in failures[:15]:
                self.stderr.write(failure)

            raise CommandError(
                "Import stopped. Existing products were NOT deleted. "
                "Fix the image URLs or connection before retrying."
            )

        def to_decimal(value, default="0"):
            value = str(value or "").strip()
            return Decimal(value) if value else Decimal(default)

        def to_bool(value):
            return str(value).strip().lower() in (
                "true", "1", "yes"
            )

        # STEP 2: Validate product values before deletion.
        try:
            for row in rows:
                to_decimal(row["price"])
                int(row["stock_quantity"])
                to_decimal(row.get("compare_price"))
                to_decimal(row.get("cost_per_item"))
        except (ValueError, ArithmeticError) as exc:
            raise CommandError(
                f"Invalid CSV product data: {exc}"
            )

        # STEP 3: Replace products in one DB transaction.
        # Protected relationships can prevent deletion.
        try:
            with transaction.atomic():
                Product.objects.filter(
                    company=company
                ).delete()

                for index, row in enumerate(rows, start=1):
                    sku = row["sku"].strip()
                    name = row["name"].strip()

                    category, _ = Category.objects.get_or_create(
                        name=row["category"].strip()
                    )

                    product = Product.objects.create(
                        company=company,
                        category=category,
                        sku=sku,
                        name=name,
                        description=row["description"].strip(),
                        short_description=(
                            row.get("short_description") or ""
                        )[:500],
                        price=to_decimal(row["price"]),
                        compare_price=(
                            to_decimal(row["compare_price"])
                            if row.get("compare_price")
                            else None
                        ),
                        cost_per_item=to_decimal(
                            row.get("cost_per_item")
                        ),
                        stock_quantity=int(
                            row["stock_quantity"]
                        ),
                        barcode=(
                            row.get("barcode") or ""
                        ).strip(),
                        weight=(
                            to_decimal(row["weight"])
                            if row.get("weight")
                            else None
                        ),
                        dimensions=(
                            row.get("dimensions") or ""
                        ).strip(),
                        is_active=to_bool(
                            row.get("is_active", "true")
                        ),
                        is_featured=to_bool(
                            row.get("is_featured", "false")
                        ),
                        is_digital=to_bool(
                            row.get("is_digital", "false")
                        ),
                    )

                    filename, content = downloaded_images[sku]

                    image = ProductImage(
                        product=product,
                        is_main=True,
                        alt_text=name,
                    )

                    image.image.save(
                        filename,
                        ContentFile(content),
                        save=True,
                    )

                    self.stdout.write(
                        f"[{index}/200] Imported: {name}"
                    )

        except (ProtectedError, RestrictedError) as exc:
            raise CommandError(
                f"Deletion blocked by related data: {exc}"
            )

        except Exception as exc:
            raise CommandError(
                f"Import failed. Database transaction rolled back: {exc}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "SUCCESS! Imported 200 products with images."
            )
        )
