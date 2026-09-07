# apps/ai_assistant/services/product_retrieval.py
"""
Hybrid product retrieval service.
Combines FAISS semantic search, PostgreSQL full-text search, and user interest
re-ranking to provide the best product matches for user queries.
"""

import logging
from typing import Dict, List, Optional, Iterable

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import connection
from django.db.models import Q
from django.urls import reverse

from apps.ai_assistant.models import UserProductInterest
from apps.products.models import Product

logger = logging.getLogger(__name__)


def _supports_postgres_fts():
    return connection.vendor == "postgresql"


# ─── PostgreSQL Full-Text Search ─────────────────────────────────────────────

def search_products_fts(query_text: str, limit: int = 10):
    """Search products using PostgreSQL FTS or icontains fallback."""
    products = Product.objects.filter(is_active=True)
    if not query_text.strip():
        return products.order_by("-total_sold", "-average_rating")[:limit]

    if _supports_postgres_fts():
        vector = (
            SearchVector("name", weight="A")
            + SearchVector("short_description", weight="B")
            + SearchVector("description", weight="C")
        )
        query = SearchQuery(query_text)
        return (
            products.annotate(rank=SearchRank(vector, query))
            .filter(rank__gte=0.02)
            .order_by("-rank", "-total_sold")[:limit]
        )

    return products.filter(
        Q(name__icontains=query_text)
        | Q(short_description__icontains=query_text)
        | Q(description__icontains=query_text)
    ).order_by("-total_sold", "-average_rating")[:limit]


# ─── User Interest Products ─────────────────────────────────────────────────

def get_user_interest_products(user, limit: int = 8):
    """Get products the user has shown positive interest in."""
    positive_types = ["view", "like"]
    return (
        Product.objects.filter(
            user_interests__user=user,
            user_interests__interest_type__in=positive_types,
        )
        .distinct()
        .order_by("-user_interests__created_at")[:limit]
    )


# ─── User Interest Re-ranking ───────────────────────────────────────────────

def rank_products_for_user(user, query_text: str, limit: int = 5) -> List[Product]:
    """Re-rank search results based on user interests."""
    candidate_products = list(search_products_fts(query_text, limit=20))
    if not candidate_products:
        return []

    interests = UserProductInterest.objects.filter(
        user=user,
        product_id__in=[p.id for p in candidate_products],
    )
    score_map = {p.id: 0.0 for p in candidate_products}

    for interest in interests:
        if interest.interest_type == "like":
            score_map[interest.product_id] += 3.0 * interest.weight
        elif interest.interest_type == "view":
            score_map[interest.product_id] += 1.0 * interest.weight
        elif interest.interest_type == "dislike":
            score_map[interest.product_id] -= 3.0 * interest.weight

    ranked = sorted(
        candidate_products,
        key=lambda p: (
            score_map.get(p.id, 0.0),
            float(p.average_rating or 0),
            p.total_sold,
        ),
        reverse=True,
    )
    return ranked[:limit]


# ─── Hybrid Search (NEW) ────────────────────────────────────────────────────

def hybrid_search(
    query: str,
    entities: Optional[Dict] = None,
    user=None,
    limit: int = 5,
) -> List[Dict]:
    """
    Perform hybrid product search combining:
    1. FAISS semantic search (embedding similarity)
    2. PostgreSQL FTS / keyword search
    3. Entity-based DB filtering (price, category, brand)
    4. User interest re-ranking

    Args:
        query: The user's search query text.
        entities: Extracted entities dict from entity_extractor.
        user: The authenticated user (for personalized ranking).
        limit: Maximum number of results.

    Returns:
        List of product dicts, ranked by combined relevance.
    """
    entities = entities or {}
    results_map = {}  # product_id -> {product_data, score}

    # ─── Source 1: FAISS semantic search ──────────────────────────────
    try:
        from apps.ai_assistant.services.embedding_service import embedding_service

        if embedding_service.is_ready or embedding_service.load_index():
            semantic_results = embedding_service.search_with_filter(
                query=query,
                top_k=limit * 2,
                category=entities.get("categories", [None])[0] if entities.get("categories") else None,
                price_min=entities.get("price_min"),
                price_max=entities.get("price_max"),
            )
            for i, product in enumerate(semantic_results):
                pid = product.get("id")
                if pid is not None:
                    score = product.get("similarity_score", 0) * 10  # Scale up
                    results_map[pid] = {
                        "product": product,
                        "score": score + (limit * 2 - i) * 0.5,  # Position bonus
                        "source": "semantic",
                    }
    except Exception as e:
        logger.debug(f"Semantic search unavailable: {e}")

    # ─── Source 2: PostgreSQL FTS / keyword search ────────────────────
    try:
        raw_query = entities.get("raw_query", query) if entities else query
        fts_products = search_products_fts(raw_query, limit=limit * 2)
        for i, product in enumerate(fts_products):
            pid = product.id
            serialized = serialize_product(product)
            if pid in results_map:
                # Boost score for products found by both methods
                results_map[pid]["score"] += 5.0 + (limit * 2 - i) * 0.3
            else:
                results_map[pid] = {
                    "product": serialized,
                    "score": 3.0 + (limit * 2 - i) * 0.3,
                    "source": "fts",
                }
    except Exception as e:
        logger.debug(f"FTS search error: {e}")

    # ─── Source 3: Entity-based DB filtering ─────────────────────────
    try:
        db_filters = Q(is_active=True)
        has_entity_filter = False

        # Category filter
        if entities.get("categories"):
            cat_q = Q()
            for cat in entities["categories"]:
                cat_q |= Q(category__name__icontains=cat)
            db_filters &= cat_q
            has_entity_filter = True

        # Price filter
        if entities.get("price_min") is not None:
            db_filters &= Q(price__gte=entities["price_min"])
            has_entity_filter = True
        if entities.get("price_max") is not None:
            db_filters &= Q(price__lte=entities["price_max"])
            has_entity_filter = True

        # Brand filter (search in name and description)
        if entities.get("brands"):
            brand_q = Q()
            for brand in entities["brands"]:
                brand_q |= Q(name__icontains=brand) | Q(description__icontains=brand)
            db_filters &= brand_q
            has_entity_filter = True

        if has_entity_filter:
            filtered_products = Product.objects.filter(db_filters).order_by(
                "-total_sold", "-average_rating"
            )[:limit * 2]
            for i, product in enumerate(filtered_products):
                pid = product.id
                serialized = serialize_product(product)
                if pid in results_map:
                    results_map[pid]["score"] += 4.0
                else:
                    results_map[pid] = {
                        "product": serialized,
                        "score": 4.0 + (limit * 2 - i) * 0.2,
                        "source": "entity_filter",
                    }
    except Exception as e:
        logger.debug(f"Entity filter error: {e}")

    # ─── User interest re-ranking ────────────────────────────────────
    if user and user.is_authenticated and results_map:
        try:
            product_ids = list(results_map.keys())
            interests = UserProductInterest.objects.filter(
                user=user, product_id__in=product_ids
            )
            for interest in interests:
                pid = interest.product_id
                if pid in results_map:
                    if interest.interest_type == "like":
                        results_map[pid]["score"] += 3.0 * interest.weight
                    elif interest.interest_type == "view":
                        results_map[pid]["score"] += 1.0 * interest.weight
                    elif interest.interest_type == "dislike":
                        results_map[pid]["score"] -= 2.0 * interest.weight
        except Exception as e:
            logger.debug(f"User interest ranking error: {e}")

    # ─── Sort by combined score and return ───────────────────────────
    sorted_results = sorted(
        results_map.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    return [item["product"] for item in sorted_results[:limit]]


# ─── Serialization ──────────────────────────────────────────────────────────

def serialize_product(product: Product) -> Dict:
    """Serialize a Product model instance to a dict."""
    data = {
        "id": product.id,
        "name": product.name,
        "price": str(product.price),
        "url": reverse("products:detail", kwargs={"slug": product.slug}),
        "category": product.category.name if product.category else "",
        "total_sold": product.total_sold or 0,
        "average_rating": float(product.average_rating or 0),
        "is_featured": product.is_featured,
    }
    if hasattr(product, "short_description") and product.short_description:
        data["description"] = product.short_description[:200]
    elif hasattr(product, "description") and product.description:
        data["description"] = product.description[:200]
    return data


def serialize_products(products: Iterable[Product]) -> List[Dict]:
    """Serialize multiple Product instances."""
    base_url = getattr(settings, "SITE_URL", "").rstrip("/")
    serialized = []
    for product in products:
        item = serialize_product(product)
        if base_url:
            item["url"] = f"{base_url}{item['url']}"
        serialized.append(item)
    return serialized
