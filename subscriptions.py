from datetime import date, datetime
from decimal import Decimal, InvalidOperation


DATE_FORMAT = "%Y-%m-%d"
UPCOMING_DAYS = 30
_UNSET = object()


def validate_name(value):
    name = value.strip()
    if not name:
        raise ValueError("Name cannot be empty.")
    return name


def validate_date(value, today=None, allow_empty=False):
    text = value.strip()
    if allow_empty and not text:
        return None

    try:
        renewal_date = datetime.strptime(text, DATE_FORMAT).date()
    except ValueError as error:
        raise ValueError("Incorrect date format.") from error

    current_date = today if today is not None else date.today()
    if renewal_date <= current_date:
        raise ValueError("Renewal date cannot be today or in the past.")
    return renewal_date.isoformat()


def validate_yes_no(value, allow_empty=False):
    text = value.strip().lower()
    if allow_empty and not text:
        return None
    if text == "yes":
        return True
    if text == "no":
        return False
    raise ValueError("Value must be either yes or no.")


def validate_optional_name(value):
    if not value.strip():
        return None
    return validate_name(value)


def validate_renewal_price(value):
    text = str(value).strip()
    try:
        price = Decimal(text)
    except InvalidOperation as error:
        raise ValueError("Price must be a valid number.") from error

    if not price.is_finite() or price < 0:
        raise ValueError("Price must be a finite, non-negative number.")
    if price.as_tuple().exponent < -2:
        raise ValueError("Price cannot have more than two decimal places.")
    return f"{price:.2f}"


def validate_currency(value):
    currency = value.strip().upper()
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        raise ValueError("Currency must be a three-letter code such as EUR.")
    return currency


def validate_price_details(renewal_price, currency):
    if renewal_price is None and currency is None:
        return None, None
    if renewal_price is None or currency is None:
        raise ValueError("Price and currency must be provided together.")
    return validate_renewal_price(renewal_price), validate_currency(currency)


def find_subscription(subscriptions, subscription_id):
    for subscription in subscriptions:
        if subscription["id"] == subscription_id:
            return subscription
    raise ValueError("Invalid ID.")


def add_subscription(
    data,
    name,
    renewal_date,
    free_trial,
    today=None,
    renewal_price=None,
    currency=None,
):
    if not isinstance(free_trial, bool):
        raise ValueError("Free-trial status must be a boolean.")

    current_date = today if today is not None else date.today()
    price, currency_code = validate_price_details(renewal_price, currency)
    subscription = {
        "id": data["next_id"],
        "name": validate_name(name),
        "date_of_addition": current_date.isoformat(),
        "renewal_date": validate_date(renewal_date, current_date),
        "free_trial": free_trial,
        "renewal_price": price,
        "currency": currency_code,
    }
    data["Subscriptions"].append(subscription)
    data["next_id"] += 1
    return subscription


def edit_subscription(
    data,
    subscription_id,
    name=None,
    renewal_date=None,
    free_trial=None,
    today=None,
    renewal_price=_UNSET,
    currency=_UNSET,
):
    subscription = find_subscription(data["Subscriptions"], subscription_id)

    new_name = subscription["name"] if name is None else validate_name(name)
    new_renewal = subscription["renewal_date"]
    if renewal_date is not None:
        new_renewal = validate_date(renewal_date, today)
    new_free_trial = subscription["free_trial"]
    if free_trial is not None:
        if not isinstance(free_trial, bool):
            raise ValueError("Free-trial status must be a boolean.")
        new_free_trial = free_trial

    if (renewal_price is _UNSET) != (currency is _UNSET):
        raise ValueError("Price and currency must be edited together.")
    new_price = subscription["renewal_price"]
    new_currency = subscription["currency"]
    if renewal_price is not _UNSET:
        new_price, new_currency = validate_price_details(
            renewal_price, currency
        )

    subscription.update({
        "name": new_name,
        "renewal_date": new_renewal,
        "free_trial": new_free_trial,
        "renewal_price": new_price,
        "currency": new_currency,
    })
    return subscription


def delete_subscription(data, subscription_id):
    subscription = find_subscription(data["Subscriptions"], subscription_id)
    data["Subscriptions"].remove(subscription)
    return subscription


def mark_subscription_renewed(data, subscription_id, next_renewal_date, today=None):
    subscription = find_subscription(data["Subscriptions"], subscription_id)
    validated_date = validate_date(next_renewal_date, today)
    subscription["renewal_date"] = validated_date
    subscription["free_trial"] = False
    return subscription


def get_renewal_groups(subscriptions, today=None, upcoming_days=UPCOMING_DAYS):
    current_date = today if today is not None else date.today()
    groups = {"overdue": [], "due_today": [], "upcoming": []}
    sorted_subscriptions = sorted(
        subscriptions,
        key=lambda item: (
            item["renewal_date"], item["name"].casefold(), item["id"]
        ),
    )

    for subscription in sorted_subscriptions:
        renewal_date = date.fromisoformat(subscription["renewal_date"])
        days_until = (renewal_date - current_date).days
        if days_until < 0:
            groups["overdue"].append(subscription)
        elif days_until == 0:
            groups["due_today"].append(subscription)
        elif days_until <= upcoming_days:
            groups["upcoming"].append(subscription)
    return groups
