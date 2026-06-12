"""
Budget threshold bot alerts — Discord webhook.
Called after an expense is created or updated.
"""
import requests
from django.conf import settings
from django.db.models import Sum
from decimal import Decimal


def send_discord_alert(message: str) -> bool:
    """Send a message to the configured Discord webhook. Returns True on success."""
    webhook_url = settings.DISCORD_WEBHOOK_URL
    if not webhook_url or "your-" in webhook_url:
        return False
    try:
        resp = requests.post(webhook_url, json={"content": message}, timeout=5)
        return resp.status_code in (200, 204)
    except Exception:
        return False


def check_and_alert(expense) -> None:
    """
    Fire a Discord alert ONLY on the single expense that causes a category's
    month-to-date total to cross its monthly_limit for the first time.

    Logic:
      current_total  = all expenses in this month for this category (including this one)
      previous_total = current_total - this expense's amount

    Alert fires when:  previous_total < limit  AND  current_total > limit
    This ensures exactly one alert per threshold crossing.
    """
    category = expense.category
    if category.monthly_limit is None:
        return

    year = expense.date.year
    month = expense.date.month

    result = (
        expense.user.expenses
        .filter(category=category, date__year=year, date__month=month)
        .aggregate(total=Sum("amount"))
    )
    month_total = result["total"] or Decimal("0.00")

    previous_total = month_total - expense.amount
    if previous_total < category.monthly_limit and month_total > category.monthly_limit:
        from datetime import date
        month_name = date(year, month, 1).strftime("%B %Y")
        message = (
            f" **Budget alert**: \"{category.name}\" is over its monthly limit.\n"
            f"Spent {month_total:.2f} / {category.monthly_limit:.2f} for {month_name}."
        )
        send_discord_alert(message)