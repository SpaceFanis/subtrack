import json
from datetime import date
from pathlib import Path

from subscriptions import validate_price_details


class StorageError(ValueError):
    """Raised when the storage file cannot be understood safely."""


def _validate_stored_date(value, field_name):
    if not isinstance(value, str):
        raise StorageError(f"'{field_name}' must be a date string.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise StorageError(
            f"'{field_name}' must use the YYYY-MM-DD format."
        ) from error
    if parsed.isoformat() != value:
        raise StorageError(f"'{field_name}' must use the YYYY-MM-DD format.")


def _validate_subscription(subscription):
    if not isinstance(subscription, dict):
        raise StorageError("Each subscription must be a JSON object.")

    required_fields = {
        "id",
        "name",
        "date_of_addition",
        "renewal_date",
        "free_trial",
        "renewal_price",
        "currency",
    }
    if not required_fields.issubset(subscription):
        raise StorageError("A subscription is missing required data.")
    if type(subscription["id"]) is not int or subscription["id"] < 1:
        raise StorageError("Each subscription must have a positive integer ID.")
    if (
        not isinstance(subscription["name"], str)
        or not subscription["name"].strip()
    ):
        raise StorageError("Each subscription must have a non-empty name.")
    _validate_stored_date(subscription["date_of_addition"], "date_of_addition")
    _validate_stored_date(subscription["renewal_date"], "renewal_date")
    if not isinstance(subscription["free_trial"], bool):
        raise StorageError(
            "Each subscription must have a boolean free_trial value."
        )

    price = subscription["renewal_price"]
    currency = subscription["currency"]
    if price is None and currency is None:
        return subscription
    if not isinstance(price, str) or not isinstance(currency, str):
        raise StorageError("Renewal price and currency must be stored together.")

    try:
        normalized_price, normalized_currency = validate_price_details(
            price, currency
        )
    except ValueError as error:
        raise StorageError(f"Invalid renewal price: {error}") from error
    if price != normalized_price or currency != normalized_currency:
        raise StorageError("Renewal price and currency must use normalized formats.")
    return subscription


def validate_data(data):
    if not isinstance(data, dict):
        raise StorageError("Storage must contain a JSON object.")
    if "Subscriptions" not in data:
        raise StorageError("Storage is missing 'Subscriptions'.")
    if not isinstance(data["Subscriptions"], list):
        raise StorageError("'Subscriptions' must be a list.")
    if "next_id" not in data:
        raise StorageError("Storage is missing 'next_id'.")
    if type(data["next_id"]) is not int:
        raise StorageError("'next_id' must be an integer.")

    subscriptions = [
        _validate_subscription(item) for item in data["Subscriptions"]
    ]
    ids = [subscription["id"] for subscription in subscriptions]
    if len(ids) != len(set(ids)):
        raise StorageError("Subscription IDs must be unique.")

    next_id = data["next_id"]
    minimum_next_id = max(ids, default=0) + 1
    if next_id < minimum_next_id:
        raise StorageError("'next_id' must be greater than all existing IDs.")
    return {"Subscriptions": subscriptions, "next_id": next_id}


def load_data(path):
    path = Path(path)
    if not path.exists():
        data = {"Subscriptions": [], "next_id": 1}
        save_data(data, path)
        return data

    try:
        with path.open("r", encoding="utf-8") as file:
            return validate_data(json.load(file))
    except json.JSONDecodeError as error:
        raise StorageError(f"Storage file contains invalid JSON: {path}") from error
    except OSError as error:
        raise StorageError(f"Could not read storage file: {path}") from error


def save_data(data, path):
    validated = validate_data(data)
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(validated, file, indent=4)
            file.write("\n")
    except OSError as error:
        raise StorageError(f"Could not write storage file: {path}") from error
