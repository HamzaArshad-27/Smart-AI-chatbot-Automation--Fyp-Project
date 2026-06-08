from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import connection
from django.db.models import Q
from django.urls import reverse

from apps.ai_assistant.models import UserProductInterest
from apps.products.models import Product


def _supports_postgres_fts():
    return connection.vendor == "postgresql"


def search_products(query_text, limit=10):
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


def get_user_interest_products(user, limit=8):
    positive_types = ["view", "like"]
    return (
        Product.objects.filter(
            user_interests__user=user,
            user_interests__interest_type__in=positive_types,
        )
        .distinct()
        .order_by("-user_interests__created_at")[:limit]
    )


def rank_products_for_user(user, query_text, limit=5):
    candidate_products = list(search_products(query_text, limit=20))
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
        key=lambda p: (score_map.get(p.id, 0.0), float(p.average_rating or 0), p.total_sold),
        reverse=True,
    )
    return ranked[:limit]


def serialize_product(product):
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "url": reverse("products:detail", kwargs={"slug": product.slug}),
    }


def serialize_products(products):
    base_url = getattr(settings, "SITE_URL", "").rstrip("/")
    serialized = []
    for product in products:
        item = serialize_product(product)
        if base_url:
            item["url"] = f"{base_url}{item['url']}"
        serialized.append(item)
    return serialized
