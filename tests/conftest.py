from datetime import date

import pytest


@pytest.fixture
def today():
    return date(2026, 1, 15)


@pytest.fixture
def empty_data():
    return {"Subscriptions": [], "next_id": 1}


@pytest.fixture
def subscription():
    return {
        "id": 1,
        "name": "Spotify",
        "date_of_addition": "2026-01-01",
        "renewal_date": "2026-02-01",
        "free_trial": False,
        "renewal_price": "10.99",
        "currency": "EUR",
    }
