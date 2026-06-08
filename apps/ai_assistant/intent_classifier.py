from apps.ai_assistant.services.ollama_client import OllamaClient


VALID_INTENTS = {
    "SHOW_CATEGORIES",
    "SEARCH_PRODUCTS",
    "SELECT_CATEGORY",
    "SHOW_FEATURED",
    "ASK_CLARIFICATION",
    "CHITCHAT",
    "UNKNOWN",
}


CLASSIFY_PROMPT = """
Classify the user's latest message for a shopping chatbot.
Return JSON only with keys: intent, keyword, category_hint.
Allowed intents:
- SHOW_CATEGORIES: generic browse requests like "show list", "what do you have", "categories"
- SEARCH_PRODUCTS: specific product/category keyword like "bags", "shirts", "beauty products", "nike shoes"
- SELECT_CATEGORY: user selects one category after categories were shown
- SHOW_FEATURED: user asks for featured/trending/popular
- ASK_CLARIFICATION: unclear shopping request needing follow-up
- CHITCHAT: greeting or casual talk
- UNKNOWN: none of the above
If user mentions a product type/category name, prefer SEARCH_PRODUCTS.
If user gives a single category-like word (e.g., "beauty", "bags", "shirts"), choose SEARCH_PRODUCTS unless awaiting_category=true.
If awaiting_category=true and user mentions category name, choose SELECT_CATEGORY.
Output format example:
{"intent":"SEARCH_PRODUCTS","keyword":"bags","category_hint":"bags"}
""".strip()


def classify_user_intent(message, history=None, awaiting_category=False):
    client = OllamaClient()
    history_text = "\n".join(
        [f"User: {h.get('message', '')}\nAssistant: {h.get('response', '')}" for h in (history or [])[-4:]]
    ) or "No history."
    prompt = (
        f"{CLASSIFY_PROMPT}\n\n"
        f"Context: awaiting_category={str(awaiting_category).lower()}\n"
        f"Recent history:\n{history_text}\n\n"
        f"Latest user message:\n{message}\n"
    )
    parsed = client.classify_with_prompt(prompt)

    intent = (parsed.get("intent") or "UNKNOWN").upper()
    if intent not in VALID_INTENTS:
        intent = "UNKNOWN"
    return {
        "intent": intent,
        "keyword": (parsed.get("keyword") or "").strip(),
        "category_hint": (parsed.get("category_hint") or "").strip(),
    }
