# apps/ai_assistant/management/commands/rebuild_embeddings.py
"""
Management command to build/rebuild the FAISS embedding index for AI product search.

Usage:
    python manage.py rebuild_embeddings
    python manage.py rebuild_embeddings --limit 500
"""

from django.core.management.base import BaseCommand

from apps.ai_assistant.data_loader import WebsiteDataLoader
from apps.ai_assistant.services.embedding_service import embedding_service


class Command(BaseCommand):
    help = "Build or rebuild the FAISS embedding index for AI product search"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=500,
            help="Maximum number of products to index (default: 500)",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        self.stdout.write(f"Loading products from database (limit={limit})...")

        products = WebsiteDataLoader.load_products(limit=limit)

        if not products:
            self.stderr.write(self.style.ERROR("No products found in the database!"))
            return

        self.stdout.write(f"Found {len(products)} products. Building embeddings...")

        success = embedding_service.build_index(products)

        if success:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully built FAISS index with {len(products)} products!"
                )
            )
        else:
            self.stderr.write(
                self.style.ERROR(
                    "Failed to build FAISS index. Check logs for details."
                )
            )
