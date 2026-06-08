import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.ai_assistant.chatbot import process_chat_message
from apps.ai_assistant.models import UserProductInterest
from apps.products.models import Product


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
