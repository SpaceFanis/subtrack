from datetime import date, timedelta

import pytest

import project
from storage import load_data, save_data
from subscriptions import add_subscription


def test_prompt_for_id_retries_non_integer_and_unknown_id(
    empty_data, today, monkeypatch, capsys
):
    add_subscription(empty_data, "Spotify", "2026-02-01", False, today)
    answers = iter(["hello", "2", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert project.prompt_for_id(empty_data["Subscriptions"]) == 1
    assert capsys.readouterr().out.count("Invalid ID") == 2


@pytest.mark.parametrize("choice", range(1, 8))
def test_menu_accepts_all_seven_choices(choice, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: str(choice))
    assert project.prompt_for_menu_choice() == choice


def test_menu_retries_invalid_values(monkeypatch, capsys):
    answers = iter(["hello", "8", "3"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert project.prompt_for_menu_choice() == 3
    output = capsys.readouterr().out
    assert "integer" in output
    assert "1 to 7" in output


def test_new_price_can_be_omitted(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert project.prompt_for_new_price() == (None, None)


def test_new_price_retries_and_normalizes(monkeypatch, capsys):
    answers = iter(["bad", "9.5", "eur"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert project.prompt_for_new_price() == ("9.50", "EUR")
    assert "valid number" in capsys.readouterr().out


def test_edit_price_blank_keeps_and_none_removes(subscription, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert project.prompt_for_edited_price(subscription) == (False, None, None)

    monkeypatch.setattr("builtins.input", lambda _: "none")
    assert project.prompt_for_edited_price(subscription) == (True, None, None)


def test_dashboard_has_all_risk_groups(capsys):
    today = date(2026, 1, 15)
    data = {
        "Subscriptions": [
            _subscription(1, "Old", "2026-01-14", True),
            _subscription(2, "Today", "2026-01-15"),
            _subscription(3, "Soon", "2026-01-20"),
        ],
        "next_id": 4,
    }

    project.print_dashboard(data, today)

    output = capsys.readouterr().out
    assert "OVERDUE" in output
    assert "DUE TODAY" in output
    assert "COMING UP IN THE NEXT 30 DAYS" in output
    assert "FREE TRIAL" in output
    assert "9.99 EUR" in output


def test_dashboard_empty_states(capsys):
    project.print_dashboard({"Subscriptions": [], "next_id": 1})
    assert "No subscriptions yet" in capsys.readouterr().out

    data = {"Subscriptions": [_subscription(1, "Later", "2099-01-01")], "next_id": 2}
    project.print_dashboard(data, date(2026, 1, 15))
    assert "No renewals due in the next 30 days" in capsys.readouterr().out


def test_mark_renewed_cli_persists_change(tmp_path, monkeypatch):
    path = tmp_path / "data.json"
    data = {"Subscriptions": [], "next_id": 1}
    add_subscription(
        data, "Trial", "2098-01-01", True, date.today(), "9.99", "EUR"
    )
    save_data(data, path)
    answers = iter(["1", "2099-01-01"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    project.mark_renewed_cli(path)

    renewed = load_data(path)["Subscriptions"][0]
    assert renewed["renewal_date"] == "2099-01-01"
    assert renewed["free_trial"] is False


def test_add_dashboard_renew_and_reload_workflow(tmp_path, monkeypatch, capsys):
    path = tmp_path / "data.json"
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    later = (date.today() + timedelta(days=60)).isoformat()
    add_answers = iter(["Netflix", tomorrow, "yes", "12.99", "eur"])
    monkeypatch.setattr("builtins.input", lambda _: next(add_answers))

    project.add_cli(path)
    restarted = load_data(path)
    project.print_dashboard(restarted)
    assert "Netflix" in capsys.readouterr().out

    renew_answers = iter(["1", later])
    monkeypatch.setattr("builtins.input", lambda _: next(renew_answers))
    project.mark_renewed_cli(path)

    final_data = load_data(path)
    subscription = final_data["Subscriptions"][0]
    assert subscription["renewal_date"] == later
    assert subscription["free_trial"] is False
    assert subscription["renewal_price"] == "12.99"
    assert subscription["currency"] == "EUR"


def test_menu_displays_seven_actions(capsys):
    project.print_menu()
    output = capsys.readouterr().out
    for choice in range(1, 8):
        assert f"{choice}." in output


def _subscription(subscription_id, name, renewal_date, free_trial=False):
    return {
        "id": subscription_id,
        "name": name,
        "date_of_addition": "2026-01-01",
        "renewal_date": renewal_date,
        "free_trial": free_trial,
        "renewal_price": "9.99",
        "currency": "EUR",
    }
