import json

import pytest

from storage import StorageError, load_data, save_data, validate_data


def test_missing_storage_is_initialized(tmp_path):
    path = tmp_path / "data.json"

    assert load_data(path) == {"Subscriptions": [], "next_id": 1}
    assert path.exists()


def test_save_and_load_round_trip(tmp_path, subscription):
    path = tmp_path / "data.json"
    data = {"Subscriptions": [subscription], "next_id": 2}

    save_data(data, path)

    assert load_data(path) == data


def test_past_renewal_date_remains_valid_storage(subscription):
    subscription["renewal_date"] = "2020-01-01"
    data = {"Subscriptions": [subscription], "next_id": 2}

    assert validate_data(data) == data


@pytest.mark.parametrize("field", ["date_of_addition", "renewal_date"])
def test_invalid_stored_dates_are_rejected(subscription, field):
    subscription[field] = "01/02/2026"
    with pytest.raises(StorageError, match="YYYY-MM-DD"):
        validate_data({"Subscriptions": [subscription], "next_id": 2})


@pytest.mark.parametrize(
    ("price", "currency"),
    [("9.99", None), (None, "EUR"), (9.99, "EUR"), ("9.9", "EUR"), ("9.99", "eur")],
)
def test_invalid_stored_price_formats_are_rejected(subscription, price, currency):
    subscription["renewal_price"] = price
    subscription["currency"] = currency
    with pytest.raises(StorageError):
        validate_data({"Subscriptions": [subscription], "next_id": 2})


def test_missing_new_schema_field_is_rejected(subscription):
    del subscription["renewal_price"]
    with pytest.raises(StorageError, match="missing required"):
        validate_data({"Subscriptions": [subscription], "next_id": 2})


def test_duplicate_ids_and_invalid_next_id_are_rejected(subscription):
    duplicate = subscription.copy()
    with pytest.raises(StorageError, match="unique"):
        validate_data({"Subscriptions": [subscription, duplicate], "next_id": 2})
    with pytest.raises(StorageError, match="greater"):
        validate_data({"Subscriptions": [subscription], "next_id": 1})


def test_saving_shorter_json_truncates_old_content(tmp_path, empty_data):
    path = tmp_path / "data.json"
    path.write_text("x" * 1_000, encoding="utf-8")

    save_data(empty_data, path)

    assert load_data(path) == empty_data


def test_malformed_json_raises_clear_error(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(StorageError, match="invalid JSON"):
        load_data(path)


@pytest.mark.parametrize(
    "content",
    [
        [],
        {},
        {"Subscriptions": {}, "next_id": 1},
        {"Subscriptions": ["not an object"], "next_id": 1},
    ],
)
def test_invalid_storage_structure_raises_clear_error(tmp_path, content):
    path = tmp_path / "data.json"
    path.write_text(json.dumps(content), encoding="utf-8")

    with pytest.raises(StorageError):
        load_data(path)
