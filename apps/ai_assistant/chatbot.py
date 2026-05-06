from django.core.cache import cache

from apps.ai_assistant.graph import build_assistant_graph
from apps.ai_assistant.models import ChatHistory


RECENT_HISTORY_LIMIT = 6
CACHE_TTL_SECONDS = 120
assistant_graph = build_assistant_graph()


def _cache_key(user_id, message):
    return f"ai_graph_chat:{user_id}:{message.strip().lower()}"


def _load_recent_messages(user):
    rows = (
        ChatHistory.objects.filter(user=user)
        .order_by("-created_at")
        .values("message", "response")[:RECENT_HISTORY_LIMIT]
    )
    rows = list(reversed(list(rows)))
    messages = []
    for row in rows:
        messages.append({"role": "user", "content": row.get("message", "")})
        messages.append({"role": "assistant", "content": row.get("response", "")})
    return messages


def process_chat_message(user, message, graph_state=None):
    normalized = (message or "").strip()
    if not normalized:
        return {"response": "Please type a message.", "suggestions": []}, graph_state or {}

    cache_key = _cache_key(user.id, normalized)
    cached = cache.get(cache_key)
    if cached:
        ChatHistory.objects.create(
            user=user,
            message=normalized,
            response=cached.get("response", ""),
            context_used={"source": "cache", "suggestions": cached.get("suggestions", [])},
        )
        return cached, (graph_state or {})

    state = graph_state or {}
    messages = state.get("messages") or _load_recent_messages(user)
    messages.append({"role": "user", "content": normalized})
    initial_state = {
        "messages": messages,
        "step": state.get("step", "initial"),
        "intent": "UNKNOWN",
        "selected_category_id": state.get("selected_category_id"),
        "last_search_keyword": state.get("last_search_keyword"),
        "products_found": [],
        "categories_shown": state.get("categories_shown", False),
        "last_response": "",
    }

    final_state = assistant_graph.invoke(initial_state)
    response_text = final_state.get("last_response") or "How can I help you shop today?"
    suggestions = final_state.get("products_found", [])[:5]
    payload = {"response": response_text, "suggestions": suggestions}
    persisted_state = {
        "messages": messages + [{"role": "assistant", "content": response_text}],
        "step": final_state.get("step", "initial"),
        "selected_category_id": final_state.get("selected_category_id"),
        "last_search_keyword": final_state.get("last_search_keyword"),
        "categories_shown": final_state.get("categories_shown", False),
    }

    ChatHistory.objects.create(
        user=user,
        message=normalized,
        response=response_text,
        context_used={
            "intent": final_state.get("intent", "UNKNOWN"),
            "step": final_state.get("step", "initial"),
            "suggestion_ids": [s.get("id") for s in suggestions if s.get("id")],
        },
    )
    cache.set(cache_key, payload, CACHE_TTL_SECONDS)
    return payload, persisted_state
