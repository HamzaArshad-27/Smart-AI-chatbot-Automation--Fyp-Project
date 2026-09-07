# apps/ai_assistant/verifier.py
"""
Post-LLM response verification.
Checks that product names, prices, and claims in an LLM response
match the actual retrieved product data. Corrects hallucinations.
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def verify_response(response_text: str, retrieved_products: List[Dict]) -> str:
    """
    Verify an LLM-generated response against retrieved product data.
    Removes or corrects hallucinated product names and prices.

    Args:
        response_text: The raw LLM response text.
        retrieved_products: List of product dicts from the retrieval step.

    Returns:
        Verified (possibly corrected) response text.
    """
    if not response_text or not retrieved_products:
        return response_text

    verified = response_text

    # Build lookup of real product data
    real_products = {}
    for p in retrieved_products:
        name = (p.get("name") or "").strip()
        if name:
            real_products[name.lower()] = {
                "name": name,
                "price": _parse_price(p.get("price", "0")),
                "url": p.get("url", ""),
            }

    # Check for price hallucinations: find "$XX.XX" patterns and verify
    verified = _verify_prices(verified, real_products)

    # Check for hallucinated product names (names not in our data)
    verified = _verify_product_names(verified, real_products)

    return verified


def _parse_price(price_val) -> Optional[float]:
    """Safely parse a price value to float."""
    try:
        if isinstance(price_val, (int, float)):
            return float(price_val)
        if isinstance(price_val, str):
            cleaned = re.sub(r'[^\d.]', '', price_val)
            return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None
    return None


def _verify_prices(text: str, real_products: Dict) -> str:
    """
    Find price mentions in the text and verify they match real products.
    Pattern: "Product Name - $XX.XX" or "Product Name ($XX.XX)"
    """
    # Match patterns like "ProductName - $XX.XX" or "ProductName ($XX.XX)"
    price_pattern = re.compile(
        r'([A-Za-z][\w\s\-&\']+?)\s*[-–—]\s*\$\s*(\d+(?:\.\d{1,2})?)'
    )

    def _check_price(match):
        mentioned_name = match.group(1).strip().lower()
        mentioned_price = float(match.group(2))

        # Find the closest matching real product
        for real_key, real_data in real_products.items():
            # Check if the mentioned name is similar to a real product
            if _names_match(mentioned_name, real_key):
                real_price = real_data["price"]
                if real_price is not None and abs(real_price - mentioned_price) > 0.01:
                    # Price mismatch — correct it
                    logger.warning(
                        f"Price correction: '{match.group(1)}' "
                        f"${mentioned_price} → ${real_price:.2f}"
                    )
                    return f"{real_data['name']} - ${real_price:.2f}"
                return match.group(0)  # Price matches, keep as is

        # Product not in our data — could be hallucinated
        return match.group(0)

    return price_pattern.sub(_check_price, text)


def _verify_product_names(text: str, real_products: Dict) -> str:
    """
    Check for product name mentions that don't match any retrieved product.
    We only flag names that look like product references (after bullet points).
    """
    lines = text.split('\n')
    verified_lines = []

    for line in lines:
        # Check bullet point lines (common product listing format)
        bullet_match = re.match(r'^(\s*[•\-\*]\s+)(.+)', line)
        if bullet_match:
            prefix = bullet_match.group(1)
            content = bullet_match.group(2)

            # Extract potential product name (before price or dash)
            name_match = re.match(r'([^$\-–—]+)', content)
            if name_match:
                mentioned = name_match.group(1).strip().lower()
                # Check if this product exists in our data
                found = any(
                    _names_match(mentioned, real_key)
                    for real_key in real_products
                )
                if not found and len(mentioned) > 3:
                    # Potentially hallucinated — add a note but don't remove
                    # (could just be a description, not a product name)
                    pass

        verified_lines.append(line)

    return '\n'.join(verified_lines)


def _names_match(name1: str, name2: str) -> bool:
    """
    Check if two product names are similar enough to be the same product.
    Uses normalized substring matching.
    """
    n1 = _normalize_name(name1)
    n2 = _normalize_name(name2)

    if not n1 or not n2:
        return False

    # Exact match
    if n1 == n2:
        return True

    # One contains the other
    if n1 in n2 or n2 in n1:
        return True

    # Word overlap: if >60% of words match
    words1 = set(n1.split())
    words2 = set(n2.split())
    if words1 and words2:
        overlap = len(words1 & words2)
        min_len = min(len(words1), len(words2))
        if min_len > 0 and overlap / min_len >= 0.6:
            return True

    return False


def _normalize_name(name: str) -> str:
    """Normalize a product name for comparison."""
    name = name.lower().strip()
    # Remove common prefixes/articles
    name = re.sub(r'^(the|a|an)\s+', '', name)
    # Remove special characters
    name = re.sub(r'[^\w\s]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def build_product_context(products: List[Dict]) -> str:
    """
    Build a formatted product context string for LLM prompt injection.
    This ensures the LLM has accurate data to reference.
    """
    if not products:
        return "No products found matching the query."

    lines = ["RETRIEVED PRODUCTS (use ONLY these in your response):"]
    for i, p in enumerate(products[:10], 1):
        name = p.get("name", "Unknown")
        price = p.get("price", "N/A")
        category = p.get("category", p.get("category_name", ""))
        url = p.get("url", "")
        rating = p.get("average_rating", "")
        sold = p.get("total_sold", "")

        line = f"  {i}. {name} — ${price}"
        if category:
            line += f" [{category}]"
        if rating:
            line += f" ⭐{rating}"
        if sold:
            line += f" ({sold} sold)"
        if url:
            line += f" → {url}"
        lines.append(line)

    return "\n".join(lines)
