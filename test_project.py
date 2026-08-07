from project import check_date, check_yes_no, get_id


def test_check_date(monkeypatch):
    provide_iterable_elements(monkeypatch, ["hello", "2018-05-05", "2028-08-03"])
    assert check_date("", False) == "2028-08-03"


def test_check_date_empty_allowed(monkeypatch):
    provide_iterable_elements(monkeypatch, ["hello", "2015-05-05", ""])
    assert check_date("", True) == None


def test_check_yes_no(monkeypatch):
    provide_iterable_elements(monkeypatch, ["5", "hello", "yes?", "non", "NO "])
    assert check_yes_no("", False) == "no"


def test_check_yes_no_empty_allowed(monkeypatch):
    provide_iterable_elements(monkeypatch, ["YE", "hi", ""])
    assert check_yes_no("", True) == None


def test_get_id(monkeypatch):
    data = {
        "Subscriptions": [
            {
                "id": 1,
                "name": "Example",
                "date_of_addition": "2026-08-04",
                "renewal_date": "2028-08-04",
                "free_trial": "no"
            }
        ]
    }
    provide_iterable_elements(monkeypatch, ["0", "hello", "1.8", "-1", "1"])
    assert get_id(data) == 1


def provide_iterable_elements(monkeypatch, test_list):
    elements = iter(test_list)
    monkeypatch.setattr("builtins.input", lambda _: next(elements))
