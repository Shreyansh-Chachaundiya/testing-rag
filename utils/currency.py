from typing import Dict, Tuple


EXCHANGE_RATES: Dict[str, float] = {
    "USD": 1.00,
    "EUR": 0.85,
    "GBP": 0.73,
    "JPY": 110.0,
    "CAD": 1.25,
    "AUD": 1.35,
    "INR": 74.5,
    "CNY": 6.45,
}

CURRENCY_SYMBOLS: Dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CAD": "C$",
    "AUD": "A$",
    "INR": "₹",
    "CNY": "¥",
}


def convert(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert amount between currencies."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency not in EXCHANGE_RATES:
        raise ValueError(f"Unsupported currency: {from_currency}")
    if to_currency not in EXCHANGE_RATES:
        raise ValueError(f"Unsupported currency: {to_currency}")

    usd_amount = amount / EXCHANGE_RATES[from_currency]
    result = usd_amount * EXCHANGE_RATES[to_currency]
    return round(result, 2)


def format_currency(amount: float, currency: str) -> str:
    """Format amount with currency symbol."""
    symbol = CURRENCY_SYMBOLS.get(currency.upper(), currency)
    return f"{symbol}{amount:,.2f}"


def get_rate(from_currency: str, to_currency: str) -> float:
    """Get exchange rate between two currencies."""
    return convert(1.0, from_currency, to_currency)


def supported_currencies() -> list:
    """List all supported currency codes."""
    return sorted(EXCHANGE_RATES.keys())
