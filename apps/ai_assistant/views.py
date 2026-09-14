import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST,require_GET
from apps.ai_assistant.chatbot import process_chat_message
from apps.ai_assistant.models import UserProductInterest
from apps.products.models import Product
from django.contrib.admin.views.decorators import staff_member_required
from apps.ai_assistant.data_loader import WebsiteDataLoader, refresh_ai_data
from django.core.cache import cache
from apps.ai_assistant.data_loader import CACHE_KEY_STATS, CACHE_KEY_CATEGORIES, CACHE_KEY_TRENDING


def _is_buyer(user):
    return getattr(user, "role", "") in {"customer", "retailer"}


@login_required
@require_POST
def chat_api(request):
    if not _is_buyer(request.user):
        return JsonResponse({"error": "Only buyers can use AI chat."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    message = (payload.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "Message is required."}, status=400)

    session_state = request.session.get("ai_graph_state", {})
    try:
        result, updated_state = process_chat_message(
            user=request.user,
            message=message,
            graph_state=session_state,
        )
        request.session["ai_graph_state"] = updated_state
        request.session.modified = True
    except Exception:
        return JsonResponse(
            {
                "response": "Sorry, the assistant is temporarily unavailable. Please try again shortly.",
                "suggestions": [],
            },
            status=503,
        )
    return JsonResponse(
        {
            "response": result.get("response", ""),
            "suggestions": result.get("suggestions", []),
        },
        status=200,
    )


@login_required
@require_POST
def track_interest_api(request):
    if not _is_buyer(request.user):
        return JsonResponse({"error": "Only buyers can track interests."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    product_id = payload.get("product_id")
    interest_type = payload.get("interest_type")
    if interest_type not in {"view", "like", "dislike"}:
        return JsonResponse({"error": "Invalid interest_type."}, status=400)

    product = Product.objects.filter(id=product_id, is_active=True).first()
    if not product:
        return JsonResponse({"error": "Product not found."}, status=404)

    UserProductInterest.objects.create(
        user=request.user,
        product=product,
        interest_type=interest_type,
        weight=2.0 if interest_type == "like" else 1.0,
        metadata={"source": "api"},
    )
    return JsonResponse({"success": True}, status=201)


####################################################

@staff_member_required
@require_POST
def refresh_data_api(request):
    """Admin endpoint to refresh AI data"""
    try:
        refresh_ai_data()
        return JsonResponse({"success": True, "message": "Data refreshed successfully"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_GET
def get_stats_api(request):
    """Get website statistics for AI"""
    stats = cache.get(CACHE_KEY_STATS)
    if not stats:
        stats = WebsiteDataLoader.load_website_stats()
    
    categories = cache.get(CACHE_KEY_CATEGORIES)
    if not categories:
        categories = WebsiteDataLoader.load_categories()
    
    trending = cache.get(CACHE_KEY_TRENDING)
    if not trending:
        trending = WebsiteDataLoader.load_trending_products()
    
    return JsonResponse({
        "stats": stats,
        "categories": categories[:10],
        "trending": trending[:5]
    })