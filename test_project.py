import json
from datetime import date

import pytest

from project import (
    add_subscription,
    delete_subscription,
    edit_subscription,
    prompt_for_id,
    validate_date,
    validate_name,
    validate_optional_name,
    validate_yes_no,
)
from storage import StorageError, load_data, save_data


TODAY = date(2026, 1, 15)


@pytest.fixture
def empty_data():
    return {"Subscriptions": [], "next_id": 1}


def test_validate_date_accepts_future_date():
    assert validate_date("2026-01-16", TODAY) == "2026-01-16"


@pytest.mark.parametrize("value", ["hello", "2026/01/16", "2026-02-30"])
def test_validate_date_rejects_invalid_dates(value):
    with pytest.raises(ValueError, match="format"):
        validate_date(value, TODAY)


@pytest.mark.parametrize("value", ["2026-01-15", "2025-12-31"])
def test_validate_date_rejects_today_and_past(value):
    with pytest.raises(ValueError, match="today or in the past"):
        validate_date(value, TODAY)


def test_optional_edit_values_allow_empty_input():
    assert validate_date("", TODAY, allow_empty=True) is None
    assert validate_yes_no("", allow_empty=True) is None
    assert validate_optional_name("   ") is None


@pytest.mark.parametrize(
    ("value", "expected"), [("YES", True), (" no ", False)]
)
def test_validate_yes_no(value, expected):
    assert validate_yes_no(value) is expected


def test_validate_yes_no_rejects_other_values():
    with pytest.raises(ValueError, match="yes or no"):
        validate_yes_no("maybe")


def test_validate_name():
    assert validate_name("  Netflix  ") == "Netflix"
    with pytest.raises(ValueError, match="empty"):
        validate_name("   ")


def test_add_subscription_generates_ids(empty_data):
    first = add_subscription(
        empty_data, "Spotify", "2026-02-01", False, TODAY
    )
    second = add_subscription(
        empty_data, "Netflix", "2026-03-01", True, TODAY
    )

    assert (first["id"], second["id"]) == (1, 2)
    assert empty_data["next_id"] == 3


def test_delete_keeps_ids_stable_and_new_id_is_unused(empty_data):
    for name in ["Spotify", "Netflix", "GitHub"]:
        add_subscription(empty_data, name, "2026-02-01", False, TODAY)

    deleted = delete_subscription(empty_data, 2)
    new = add_subscription(
        empty_data, "YouTube", "2026-02-01", False, TODAY
    )

    assert deleted["name"] == "Netflix"
    assert [item["id"] for item in empty_data["Subscriptions"]] == [1, 3, 4]
    assert new["id"] == 4


def test_delete_rejects_unknown_id(empty_data):
    with pytest.raises(ValueError, match="Invalid ID"):
        delete_subscription(empty_data, 99)


def test_prompt_for_id_retries_non_integer_and_unknown_id(
    empty_data, monkeypatch
):
    add_subscription(empty_data, "Spotify", "2026-02-01", False, TODAY)
    answers = iter(["hello", "2", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert prompt_for_id(empty_data["Subscriptions"]) == 1


def test_edit_updates_correct_record_and_preserves_other_fields(empty_data):
    first = add_subscription(
        empty_data, "Spotify", "2026-02-01", False, TODAY
    )
    second = add_subscription(
        empty_data, "Netflix", "2026-03-01", True, TODAY
    )

    edit_subscription(
        empty_data, 2, renewal_date="2026-04-01", today=TODAY
    )

    assert first["renewal_date"] == "2026-02-01"
    assert second == {
        "id": 2,
        "name": "Netflix",
        "date_of_addition": "2026-01-15",
        "renewal_date": "2026-04-01",
        "free_trial": True,
    }


def test_missing_storage_is_initialized(tmp_path):
    path = tmp_path / "data.json"
    assert load_data(path) == {"Subscriptions": [], "next_id": 1}
    assert path.exists()


def test_save_and_load_round_trip(tmp_path, empty_data):
    path = tmp_path / "data.json"
    add_subscription(empty_data, "Spotify", "2026-02-01", False, TODAY)
    save_data(empty_data, path)

    assert load_data(path) == empty_data


def test_complete_crud_workflow_persists_across_loads(tmp_path):
    path = tmp_path / "data.json"
    data = load_data(path)
    add_subscription(data, "Spotify", "2026-02-01", False, TODAY)
    add_subscription(data, "Netflix", "2026-03-01", True, TODAY)
    save_data(data, path)

    restarted = load_data(path)
    edit_subscription(restarted, 1, name="Spotify Premium")
    delete_subscription(restarted, 2)
    added = add_subscription(
        restarted, "GitHub", "2026-04-01", False, TODAY
    )
    save_data(restarted, path)

    final_data = load_data(path)
    assert added["id"] == 3
    assert final_data["Subscriptions"] == [
        {
            "id": 1,
            "name": "Spotify Premium",
            "date_of_addition": "2026-01-15",
            "renewal_date": "2026-02-01",
            "free_trial": False,
        },
        {
            "id": 3,
            "name": "GitHub",
            "date_of_addition": "2026-01-15",
            "renewal_date": "2026-04-01",
            "free_trial": False,
        },
    ]


def test_load_normalizes_legacy_free_trial_and_next_id(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(
        json.dumps({
            "Subscriptions": [{
                "id": 3,
                "name": "GitHub",
                "date_of_addition": "2026-01-01",
                "renewal_date": "2026-02-01",
                "free_trial": "yes",
            }]
        }),
        encoding="utf-8",
    )

    data = load_data(path)
    assert data["Subscriptions"][0]["free_trial"] is True
    assert data["next_id"] == 4


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
    [[], {}, {"Subscriptions": {}}, {"Subscriptions": ["not an object"]}],
)
def test_invalid_storage_structure_raises_clear_error(tmp_path, content):
    path = tmp_path / "data.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    with pytest.raises(StorageError):
        load_data(path)
