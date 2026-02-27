from typing import Dict, Any, List

from utils.currency import convert, format_currency, get_rate


class PriceFormatter:
    """Format and convert prices for multi-currency display."""

    def __init__(self, base_currency: str = "USD"):
        self.base_currency = base_currency.upper()

    def format_product_price(
        self, price: float, target_currency: str = None
    ) -> Dict[str, Any]:
        """Format a single product price."""
        target = target_currency or self.base_currency
        converted = convert(price, self.base_currency, target)

        return {
            "original": format_currency(price, self.base_currency),
            "converted": format_currency(converted, target),
            "currency": target,
            "rate": get_rate(self.base_currency, target),
        }

    def format_price_list(
        self, prices: List[float], target_currency: str = None
    ) -> List[Dict[str, Any]]:
        """Format multiple prices."""
        return [self.format_product_price(p, target_currency) for p in prices]

    def format_cart_total(
        self, items: List[Dict[str, Any]], target_currency: str = None
    ) -> Dict[str, Any]:
        """Format a cart total with conversion."""
        subtotal = sum(
            item.get("price", 0) * item.get("quantity", 1) for item in items
        )
        target = target_currency or self.base_currency
        converted = convert(subtotal, self.base_currency, target)

        return {
            "subtotal": format_currency(subtotal, self.base_currency),
            "converted_total": format_currency(converted, target),
            "item_count": len(items),
            "currency": target,
        }
