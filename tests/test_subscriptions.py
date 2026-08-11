from datetime import date

import pytest

from subscriptions import (
    add_subscription,
    delete_subscription,
    edit_subscription,
    get_renewal_groups,
    mark_subscription_renewed,
    validate_currency,
    validate_date,
    validate_name,
    validate_optional_name,
    validate_price_details,
    validate_renewal_price,
    validate_yes_no,
)


def test_validate_date_accepts_future_date(today):
    assert validate_date("2026-01-16", today) == "2026-01-16"


@pytest.mark.parametrize("value", ["hello", "2026/01/16", "2026-02-30"])
def test_validate_date_rejects_invalid_dates(value, today):
    with pytest.raises(ValueError, match="format"):
        validate_date(value, today)


@pytest.mark.parametrize("value", ["2026-01-15", "2025-12-31"])
def test_validate_date_rejects_today_and_past(value, today):
    with pytest.raises(ValueError, match="today or in the past"):
        validate_date(value, today)


def test_optional_edit_values_allow_empty_input(today):
    assert validate_date("", today, allow_empty=True) is None
    assert validate_yes_no("", allow_empty=True) is None
    assert validate_optional_name("   ") is None


def test_name_and_yes_no_validation():
    assert validate_name("  Netflix  ") == "Netflix"
    assert validate_yes_no(" YES ") is True
    assert validate_yes_no("no") is False
    with pytest.raises(ValueError, match="empty"):
        validate_name("   ")
    with pytest.raises(ValueError, match="yes or no"):
        validate_yes_no("maybe")


@pytest.mark.parametrize(
    ("value", "expected"),
    [("9", "9.00"), ("9.5", "9.50"), ("0", "0.00"), ("12.99", "12.99")],
)
def test_price_is_normalized(value, expected):
    assert validate_renewal_price(value) == expected


@pytest.mark.parametrize("value", ["abc", "-1", "1.234", "NaN", "Infinity"])
def test_invalid_prices_are_rejected(value):
    with pytest.raises(ValueError):
        validate_renewal_price(value)


def test_currency_is_normalized_and_validated():
    assert validate_currency(" eur ") == "EUR"
    for value in ["EU", "EURO", "12A", "€€€"]:
        with pytest.raises(ValueError, match="three-letter"):
            validate_currency(value)


def test_price_and_currency_must_be_provided_together():
    assert validate_price_details(None, None) == (None, None)
    with pytest.raises(ValueError, match="together"):
        validate_price_details("9.99", None)
    with pytest.raises(ValueError, match="together"):
        validate_price_details(None, "EUR")


def test_add_subscription_generates_ids_and_complete_schema(empty_data, today):
    first = add_subscription(
        empty_data, "Spotify", "2026-02-01", False, today, "9.5", "eur"
    )
    second = add_subscription(
        empty_data, "Netflix", "2026-03-01", True, today
    )

    assert first == {
        "id": 1,
        "name": "Spotify",
        "date_of_addition": "2026-01-15",
        "renewal_date": "2026-02-01",
        "free_trial": False,
        "renewal_price": "9.50",
        "currency": "EUR",
    }
    assert second["id"] == 2
    assert second["renewal_price"] is None
    assert empty_data["next_id"] == 3


def test_edit_preserves_fields_and_can_remove_price(empty_data, today):
    original = add_subscription(
        empty_data, "Spotify", "2026-02-01", True, today, "10.99", "EUR"
    )
    date_added = original["date_of_addition"]

    edited = edit_subscription(
        empty_data,
        1,
        name="Spotify Premium",
        renewal_price=None,
        currency=None,
    )

    assert edited["name"] == "Spotify Premium"
    assert edited["date_of_addition"] == date_added
    assert edited["renewal_date"] == "2026-02-01"
    assert edited["free_trial"] is True
    assert edited["renewal_price"] is None
    assert edited["currency"] is None


def test_invalid_edit_does_not_partially_modify_subscription(empty_data, today):
    subscription = add_subscription(
        empty_data, "Spotify", "2026-02-01", False, today
    )
    before = subscription.copy()

    with pytest.raises(ValueError):
        edit_subscription(
            empty_data,
            1,
            name="Changed",
            renewal_price="bad",
            currency="EUR",
        )

    assert subscription == before


def test_delete_keeps_ids_stable_and_new_id_is_unused(empty_data, today):
    for name in ["Spotify", "Netflix", "GitHub"]:
        add_subscription(empty_data, name, "2026-02-01", False, today)

    deleted = delete_subscription(empty_data, 2)
    new = add_subscription(empty_data, "YouTube", "2026-02-01", False, today)

    assert deleted["name"] == "Netflix"
    assert [item["id"] for item in empty_data["Subscriptions"]] == [1, 3, 4]
    assert new["id"] == 4


def test_mark_renewed_updates_date_and_ends_trial(empty_data, today):
    added = add_subscription(
        empty_data, "Trial", "2026-02-01", True, today, "12.99", "EUR"
    )
    renewed = mark_subscription_renewed(
        empty_data, 1, "2026-03-01", today
    )

    assert renewed["renewal_date"] == "2026-03-01"
    assert renewed["free_trial"] is False
    assert renewed["renewal_price"] == "12.99"
    assert renewed["currency"] == "EUR"
    assert renewed is added


def test_renewal_groups_apply_boundaries_and_sorting():
    today = date(2026, 1, 15)
    subscriptions = [
        _subscription(1, "31 days", "2026-02-15"),
        _subscription(2, "Today", "2026-01-15"),
        _subscription(3, "Thirty", "2026-02-14"),
        _subscription(4, "Overdue", "2026-01-14"),
        _subscription(5, "alpha", "2026-01-16"),
        _subscription(6, "Alpha", "2026-01-16"),
    ]

    groups = get_renewal_groups(subscriptions, today)

    assert [item["id"] for item in groups["overdue"]] == [4]
    assert [item["id"] for item in groups["due_today"]] == [2]
    assert [item["id"] for item in groups["upcoming"]] == [5, 6, 3]


def _subscription(subscription_id, name, renewal_date):
    return {
        "id": subscription_id,
        "name": name,
        "date_of_addition": "2026-01-01",
        "renewal_date": renewal_date,
        "free_trial": False,
        "renewal_price": None,
        "currency": None,
    }
