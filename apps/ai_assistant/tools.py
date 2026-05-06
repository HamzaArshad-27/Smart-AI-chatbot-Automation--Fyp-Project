from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import connection
from django.db.models import Q
from django.urls import reverse
import re

from apps.products.models import Category, Product


def _serialize_product(product):
    return {
        "id": product.id,
        "name": product.name,
        "price": str(product.price),
        "slug": product.slug,
        "url": reverse("products:detail", args=[product.slug]),
        "absolute_url": reverse("products:detail", args=[product.slug]),
        "category_name": product.category.name if getattr(product, "category_id", None) else "",
    }


def get_all_categories(limit=20):
    rows = (
        Category.objects.filter(is_active=True)
        .order_by("name")[:limit]
    )
    return [{"id": row.id, "name": row.name, "slug": row.slug} for row in rows]


def extract_category_keyword(user_message, categories_list):
    message = (user_message or "").strip().lower()
    if not message:
        return None

    names = [item["name"] if isinstance(item, dict) else str(item) for item in categories_list]
    normalized = [name.strip() for name in names if name and name.strip()]

    # Whole-word match first.
    for category_name in normalized:
        pattern = rf"\b{re.escape(category_name.lower())}\b"
        if re.search(pattern, message):
            return category_name

    # Fallback substring match.
    for category_name in normalized:
        if category_name.lower() in message:
            return category_name

    return None


def get_products_by_category(category_input, limit=5):
    if not category_input:
        return []

    category = None
    try:
        category_id = int(str(category_input).strip())
        category = Category.objects.filter(is_active=True, id=category_id).first()
    except (TypeError, ValueError):
        category_id = None

    if not category:
        categories = get_all_categories(limit=200)
        matched_name = extract_category_keyword(str(category_input), categories)
        if matched_name:
            category = Category.objects.filter(is_active=True, name__iexact=matched_name).first()
        else:
            # Last chance: direct loose contains on raw input.
            category = Category.objects.filter(is_active=True, name__icontains=str(category_input).strip()).first()

    if not category:
        return []
    rows = (
        Product.objects.filter(is_active=True, category=category)
        .order_by("-is_featured", "-total_sold", "-created_at")[:limit]
    )
    return [_serialize_product(row) for row in rows]


def search_products(keyword, limit=5):
    keyword = (keyword or "").strip()
    if not keyword:
        return []
    base = Product.objects.filter(is_active=True)
    if connection.vendor == "postgresql":
        vector = (
            SearchVector("name", weight="A")
            + SearchVector("short_description", weight="B")
            + SearchVector("description", weight="C")
            + SearchVector("category__name", weight="B")
        )
        query = SearchQuery(keyword)
        rows = (
            base.annotate(rank=SearchRank(vector, query))
            .filter(rank__gte=0.01)
            .order_by("-rank", "-total_sold", "-created_at")[:limit]
        )
    else:
        rows = (
            base.filter(
                Q(name__icontains=keyword)
                | Q(short_description__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(category__name__icontains=keyword)
            )
            .order_by("-is_featured", "-total_sold", "-created_at")[:limit]
        )
    return [_serialize_product(row) for row in rows]


def get_featured_products(limit=5):
    base = Product.objects.filter(is_active=True)
    rows = list(base.filter(is_featured=True).order_by("-updated_at")[:limit])
    if not rows:
        rows = list(base.order_by("-total_sold", "-average_rating", "-created_at")[:limit])
    return [_serialize_product(row) for row in rows]
