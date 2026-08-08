import json
from pathlib import Path


EMPTY_DATA = {"Subscriptions": [], "next_id": 1}


class StorageError(ValueError):
    """Raised when the storage file cannot be understood safely."""


def _normalize_free_trial(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"yes", "no"}:
        return value.lower() == "yes"
    raise StorageError("Each subscription must have a valid free_trial value.")


def _normalize_subscription(subscription):
    if not isinstance(subscription, dict):
        raise StorageError("Each subscription must be a JSON object.")

    required_fields = {
        "id", "name", "date_of_addition", "renewal_date", "free_trial"
    }
    if not required_fields.issubset(subscription):
        raise StorageError("A subscription is missing required data.")
    if not isinstance(subscription["id"], int) or subscription["id"] < 1:
        raise StorageError("Each subscription must have a positive integer ID.")
    if not isinstance(subscription["name"], str) or not subscription["name"].strip():
        raise StorageError("Each subscription must have a non-empty name.")

    normalized = subscription.copy()
    normalized["name"] = normalized["name"].strip()
    normalized["free_trial"] = _normalize_free_trial(
        normalized["free_trial"]
    )
    return normalized


def normalize_data(data):
    if not isinstance(data, dict):
        raise StorageError("Storage must contain a JSON object.")
    if "Subscriptions" not in data:
        raise StorageError("Storage is missing 'Subscriptions'.")
    if not isinstance(data["Subscriptions"], list):
        raise StorageError("'Subscriptions' must be a list.")

    subscriptions = [
        _normalize_subscription(item) for item in data["Subscriptions"]
    ]
    ids = [subscription["id"] for subscription in subscriptions]
    if len(ids) != len(set(ids)):
        raise StorageError("Subscription IDs must be unique.")

    minimum_next_id = max(ids, default=0) + 1
    next_id = data.get("next_id", minimum_next_id)
    if not isinstance(next_id, int) or next_id < minimum_next_id:
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
            return normalize_data(json.load(file))
    except json.JSONDecodeError as error:
        raise StorageError(f"Storage file contains invalid JSON: {path}") from error
    except OSError as error:
        raise StorageError(f"Could not read storage file: {path}") from error


def save_data(data, path):
    normalized = normalize_data(data)
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(normalized, file, indent=4)
            file.write("\n")
    except OSError as error:
        raise StorageError(f"Could not write storage file: {path}") from error
