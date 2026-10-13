# apps/ai_assistant/services/embedding_service.py
"""
Embedding-based semantic search using sentence-transformers and FAISS.
Provides vector similarity search for product queries.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = getattr(settings, "AI_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = getattr(settings, "AI_EMBEDDING_DIMENSION", 384)
INDEX_DIR = Path(getattr(settings, "AI_EMBEDDING_INDEX_PATH", Path(settings.BASE_DIR) / "ai_embeddings"))
INDEX_FILE = INDEX_DIR / "product_index.faiss"
METADATA_FILE = INDEX_DIR / "product_metadata.json"


class EmbeddingService:
    """
    Manages product embeddings and FAISS index for semantic search.

    Usage:
        service = EmbeddingService()
        service.load_index()  # Load existing index
        results = service.search("comfortable running shoes", top_k=5)
    """

    def __init__(self):
        self._model = None
        self._index = None
        self._product_metadata: List[Dict] = []
        self._ready = False

    @property
    def model(self):
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
                self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)
                logger.info("Embedding model loaded successfully")
            except ImportError:
                logger.error(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
                raise
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return self._model

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode a list of text strings into embedding vectors."""
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def build_index(self, products: List[Dict]) -> bool:
        """
        Build a FAISS index from a list of product dicts.

        Each product should have at minimum: id, name, price, category/category_name.
        """
        try:
            import faiss
        except ImportError:
            logger.error("faiss-cpu not installed. Run: pip install faiss-cpu")
            return False

        if not products:
            logger.warning("No products provided to build index")
            return False

        logger.info(f"Building FAISS index for {len(products)} products...")

        # Build embedding text for each product
        texts = []
        metadata = []
        for p in products:
            name = p.get("name", "")
            category = p.get("category", p.get("category_name", ""))
            description = p.get("description", p.get("short_description", ""))
            price = p.get("price", "")

            # Combine fields for rich embedding
            embed_text = f"{name}"
            if category:
                embed_text += f" | {category}"
            if description:
                # Truncate long descriptions
                desc_clean = description[:200].strip()
                embed_text += f" | {desc_clean}"

            texts.append(embed_text)
            metadata.append({
                "id": p.get("id"),
                "name": name,
                "price": str(price),
                "category": category,
                "url": p.get("url", ""),
                "total_sold": p.get("total_sold", 0),
                "average_rating": float(p.get("average_rating", 0) or 0),
                "is_featured": p.get("is_featured", False),
                "description": (description or "")[:200],
            })

        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = self.encode(texts)

        # Build FAISS index (Inner Product for cosine similarity with normalized vectors)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings.astype(np.float32))

        # Save to disk
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(INDEX_FILE))
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        self._index = index
        self._product_metadata = metadata
        self._ready = True

        logger.info(
            f"FAISS index built and saved: {len(products)} products, "
            f"dimension={dim}, index_file={INDEX_FILE}"
        )
        return True

    def load_index(self) -> bool:
        """Load an existing FAISS index from disk."""
        try:
            import faiss
        except ImportError:
            logger.warning("faiss-cpu not installed — semantic search disabled")
            return False

        if not INDEX_FILE.exists() or not METADATA_FILE.exists():
            logger.warning(
                f"FAISS index not found at {INDEX_FILE}. "
                "Run 'python manage.py rebuild_embeddings' to create it."
            )
            return False

        try:
            self._index = faiss.read_index(str(INDEX_FILE))
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                self._product_metadata = json.load(f)
            self._ready = True
            logger.info(
                f"FAISS index loaded: {self._index.ntotal} products"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return False

    @property
    def is_ready(self) -> bool:
        """Check if the index is loaded and ready for search."""
        return self._ready and self._index is not None

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for products semantically similar to the query.

        Returns list of product metadata dicts with added 'score' field,
        sorted by relevance (highest score first).
        """
        if not self.is_ready:
            # Try to load index if not ready
            if not self.load_index():
                return []

        try:
            # Encode the query
            query_vec = self.encode([query])

            # Search FAISS
            scores, indices = self._index.search(
                query_vec.astype(np.float32), min(top_k, self._index.ntotal)
            )

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self._product_metadata):
                    continue
                product = self._product_metadata[idx].copy()
                product["similarity_score"] = float(score)
                results.append(product)

            return results

        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return []

    def search_with_filter(
        self,
        query: str,
        top_k: int = 10,
        category: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
    ) -> List[Dict]:
        """
        Semantic search with post-filtering by category and price.
        Retrieves more candidates than top_k, then filters.
        """
        # Retrieve extra candidates to allow for filtering
        candidates = self.search(query, top_k=top_k * 3)

        filtered = []
        for product in candidates:
            # Category filter
            if category:
                prod_cat = (product.get("category") or "").lower()
                if category.lower() not in prod_cat:
                    continue

            # Price filter
            try:
                price = float(product.get("price", 0))
            except (ValueError, TypeError):
                price = 0

            if price_min is not None and price < price_min:
                continue
            if price_max is not None and price > price_max:
                continue

            filtered.append(product)

            if len(filtered) >= top_k:
                break

        return filtered


# ─── Singleton instance ──────────────────────────────────────────────────────
embedding_service = EmbeddingService()
