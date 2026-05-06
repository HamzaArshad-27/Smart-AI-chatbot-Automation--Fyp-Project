from typing import Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from apps.ai_assistant.intent_classifier import classify_user_intent
from apps.ai_assistant.services.ollama_client import OllamaClient
from apps.ai_assistant.tools import (
    extract_category_keyword,
    get_all_categories,
    get_featured_products,
    get_products_by_category,
    search_products,
)


class AssistantState(TypedDict):
    messages: List[Dict[str, str]]
    step: str
    intent: str
    selected_category_id: Optional[int]
    last_search_keyword: Optional[str]
    products_found: List[Dict]
    categories_shown: bool
    last_response: str


def _latest_user_message(state: AssistantState) -> str:
    for item in reversed(state.get("messages", [])):
        if item.get("role") == "user":
            return item.get("content", "").strip()
    return ""


def _format_product_lines(products: List[Dict]) -> str:
    # Keep plain-text fallback helper (no HTML), but product rendering should happen in frontend cards.
    lines = []
    for product in products:
        try:
            price_value = float(product.get("price", 0))
            lines.append(f'- {product.get("name", "Product")} - ${price_value:.2f}')
        except (TypeError, ValueError):
            lines.append(f'- {product.get("name", "Product")}')
    return "\n".join(lines)


def entry_node(state: AssistantState):
    if state.get("step") == "awaiting_category":
        return {"intent": "SELECT_CATEGORY"}
    return {"intent": "ROUTE_INITIAL"}


def classify_intent_node(state: AssistantState):
    latest = _latest_user_message(state)
    history_rows = []
    for i in range(0, len(state.get("messages", [])) - 1, 2):
        user_row = state["messages"][i]
        bot_row = state["messages"][i + 1] if i + 1 < len(state["messages"]) else {"content": ""}
        history_rows.append({"message": user_row.get("content", ""), "response": bot_row.get("content", "")})
    result = classify_user_intent(
        message=latest,
        history=history_rows[-5:],
        awaiting_category=(state.get("step") == "awaiting_category"),
    )
    return {
        "intent": result["intent"],
        "last_search_keyword": result.get("keyword") or latest,
    }


def show_categories_node(state: AssistantState):
    categories = get_all_categories(limit=20)
    if not categories:
        return {
            "last_response": "I couldn't load categories right now. Would you like to see featured products instead?",
            "step": "initial",
            "products_found": [],
        }
    names = ", ".join([category["name"] for category in categories])
    return {
        "last_response": f"Available categories: {names}. Please type a category name to continue.",
        "step": "awaiting_category",
        "categories_shown": True,
        "products_found": [],
    }


def handle_category_selection_node(state: AssistantState):
    latest = _latest_user_message(state)
    categories = get_all_categories(limit=200)
    matched_category = extract_category_keyword(latest, categories)
    if not matched_category:
        names = ", ".join([category["name"] for category in categories[:20]])
        return {
            "last_response": (
                "I couldn't identify the category from your message. "
                f"Available categories: {names}. Please type one category name."
            ),
            "step": "awaiting_category",
            "products_found": [],
        }

    products = get_products_by_category(matched_category, limit=5)
    if not products:
        names = ", ".join([category["name"] for category in categories[:20]])
        return {
            "last_response": (
                f"No products found in {matched_category}. Would you like to try another category? "
                f"Available categories: {names}."
            ),
            "step": "awaiting_category",
            "products_found": [],
        }
    return {
        "last_response": f"Great choice. Here are products in {matched_category}:",
        "step": "initial",
        "products_found": products,
    }


def search_products_node(state: AssistantState):
    keyword = state.get("last_search_keyword") or _latest_user_message(state)
    products = search_products(keyword, limit=5)
    if not products:
        return {
            "last_response": "I couldn't find matching products. Try another keyword or ask for categories.",
            "step": "initial",
            "products_found": [],
        }
    return {
        "last_response": f"Here are matching products for '{keyword}':",
        "step": "initial",
        "products_found": products,
    }


def show_featured_node(state: AssistantState):
    products = get_featured_products(limit=5)
    if not products:
        return {
            "last_response": "No featured products are available right now. Want to browse categories instead?",
            "step": "initial",
            "products_found": [],
        }
    return {
        "last_response": "Here are our featured products:",
        "step": "initial",
        "products_found": products,
    }


def ask_clarification_node(state: AssistantState):
    latest = _latest_user_message(state)
    client = OllamaClient()
    result = client.generate_conversation_json(
        user_message=latest,
        chat_history=[],
        runtime_context=(
            "Ask one short clarification question for shopping assistance. "
            "Do not invent product names. Keep it under 25 words."
        ),
    )
    return {
        "last_response": result.get("reply") or "Sure, what category or product type are you interested in?",
        "step": "initial",
        "products_found": [],
    }


def handle_chitchat_node(state: AssistantState):
    latest = _latest_user_message(state)
    client = OllamaClient()
    result = client.generate_conversation_json(
        user_message=latest,
        chat_history=[],
        runtime_context=(
            "Respond warmly to chitchat in one short sentence, then ask what products user wants."
        ),
    )
    return {
        "last_response": result.get("reply") or "I'm great, thanks! What products are you looking for today?",
        "step": "initial",
        "products_found": [],
    }


def fallback_node(state: AssistantState):
    return {
        "last_response": "I can show categories, featured items, or search by keyword. What would you like?",
        "step": "initial",
        "products_found": [],
    }


def _entry_router(state: AssistantState):
    if state.get("intent") == "SELECT_CATEGORY":
        return "SELECT_CATEGORY"
    return "ROUTE_INITIAL"


def _intent_router(state: AssistantState):
    return state.get("intent", "UNKNOWN")


def build_assistant_graph():
    workflow = StateGraph(AssistantState)
    workflow.add_node("entry_node", entry_node)
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("show_categories", show_categories_node)
    workflow.add_node("handle_category_selection", handle_category_selection_node)
    workflow.add_node("search_products", search_products_node)
    workflow.add_node("show_featured", show_featured_node)
    workflow.add_node("ask_clarification", ask_clarification_node)
    workflow.add_node("handle_chitchat", handle_chitchat_node)
    workflow.add_node("fallback", fallback_node)

    workflow.set_entry_point("entry_node")
    workflow.add_conditional_edges(
        "entry_node",
        _entry_router,
        {
            "SELECT_CATEGORY": "handle_category_selection",
            "ROUTE_INITIAL": "classify_intent",
        },
    )
    workflow.add_conditional_edges(
        "classify_intent",
        _intent_router,
        {
            "SHOW_CATEGORIES": "show_categories",
            "SEARCH_PRODUCTS": "search_products",
            "SELECT_CATEGORY": "handle_category_selection",
            "SHOW_FEATURED": "show_featured",
            "ASK_CLARIFICATION": "ask_clarification",
            "CHITCHAT": "handle_chitchat",
            "UNKNOWN": "fallback",
        },
    )
    workflow.add_edge("show_categories", END)
    workflow.add_edge("handle_category_selection", END)
    workflow.add_edge("search_products", END)
    workflow.add_edge("show_featured", END)
    workflow.add_edge("ask_clarification", END)
    workflow.add_edge("handle_chitchat", END)
    workflow.add_edge("fallback", END)
    return workflow.compile()
