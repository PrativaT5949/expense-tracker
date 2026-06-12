"""
Currency conversion helper.
Fetches live exchange rates from open.er-api.com (no API key needed).
"""
import requests
from django.conf import settings


def get_rate(from_currency: str, base_currency: str = None) -> tuple:
    """
    Returns (rate, as_of_date).
    amount_in_base = amount_in_from_currency * rate
    """
    if base_currency is None:
        base_currency = settings.BASE_CURRENCY

    from_currency = from_currency.upper()
    base_currency = base_currency.upper()

    from datetime import date
    today = str(date.today())

    if from_currency == base_currency:
        return 1.0, today

    try:
        url = f"https://open.er-api.com/v6/latest/{base_currency}"
        resp = requests.get(url, timeout=5)
        data = resp.json()

        if data.get("result") == "success":
            rates = data["rates"]
            if from_currency in rates:
                # rates[from_currency] = how many from_currency in 1 base_currency
                # we want the inverse: how many base_currency in 1 from_currency
                rate = 1.0 / rates[from_currency]
                return rate, today
    except Exception:
        pass

    # If anything fails, return 1.0 so the API doesn't crash
    return 1.0, today


def convert(amount: float, from_currency: str, base_currency: str = None) -> tuple:
    """Returns (converted_amount, rate, as_of_date)."""
    rate, as_of = get_rate(from_currency, base_currency)
    return round(amount * rate, 2), rate, as_of