import sys
from datetime import date, datetime
from pathlib import Path

from storage import StorageError, load_data, save_data


DATA_FILE = Path(__file__).with_name("data.json")
DATE_FORMAT = "%Y-%m-%d"


def validate_name(value):
    """Return a cleaned subscription name, or raise ValueError."""
    name = value.strip()
    if not name:
        raise ValueError("Name cannot be empty.")
    return name


def validate_date(value, today=None, allow_empty=False):
    """Validate and normalize a future date in YYYY-MM-DD format."""
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
    """Convert yes/no text to a boolean."""
    text = value.strip().lower()
    if allow_empty and not text:
        return None
    if text == "yes":
        return True
    if text == "no":
        return False
    raise ValueError("Value must be either yes or no.")


def find_subscription(subscriptions, subscription_id):
    for subscription in subscriptions:
        if subscription["id"] == subscription_id:
            return subscription
    raise ValueError("Invalid ID.")


def add_subscription(data, name, renewal_date, free_trial, today=None):
    current_date = today if today is not None else date.today()
    subscription = {
        "id": data["next_id"],
        "name": validate_name(name),
        "date_of_addition": current_date.isoformat(),
        "renewal_date": validate_date(renewal_date, current_date),
        "free_trial": free_trial,
    }
    if not isinstance(free_trial, bool):
        raise ValueError("Free-trial status must be a boolean.")

    data["Subscriptions"].append(subscription)
    data["next_id"] += 1
    return subscription


def edit_subscription(
    data, subscription_id, name=None, renewal_date=None, free_trial=None,
    today=None,
):
    subscription = find_subscription(data["Subscriptions"], subscription_id)
    if name is not None:
        subscription["name"] = validate_name(name)
    if renewal_date is not None:
        subscription["renewal_date"] = validate_date(renewal_date, today)
    if free_trial is not None:
        if not isinstance(free_trial, bool):
            raise ValueError("Free-trial status must be a boolean.")
        subscription["free_trial"] = free_trial
    return subscription


def delete_subscription(data, subscription_id):
    subscription = find_subscription(data["Subscriptions"], subscription_id)
    data["Subscriptions"].remove(subscription)
    return subscription


def prompt_until_valid(prompt, validator, **validator_options):
    while True:
        try:
            return validator(input(prompt), **validator_options)
        except ValueError as error:
            print(error)


def prompt_for_id(subscriptions):
    while True:
        try:
            subscription_id = int(input("Enter ID: "))
            find_subscription(subscriptions, subscription_id)
            return subscription_id
        except (ValueError, TypeError):
            print("Invalid ID. Enter an existing integer ID.")


def format_subscription(subscription, with_id=False):
    prefix = f"ID: {subscription['id']}, " if with_id else ""
    free_trial = "yes" if subscription["free_trial"] else "no"
    return (
        f"{prefix}Name: {subscription['name']} | "
        f"Date of Addition: {subscription['date_of_addition']} | "
        f"Renewal Date: {subscription['renewal_date']} | "
        f"Free Trial: {free_trial}"
    )


def print_subscriptions(subscriptions, with_id=False):
    for subscription in subscriptions:
        print(format_subscription(subscription, with_id))


def add_cli(data_path=DATA_FILE):
    print("------------------\nADD SUBSCRIPTION\n")
    name = prompt_until_valid("Name: ", validate_name)
    current_date = date.today()
    print(f"Current date: {current_date:%Y-%m-%d}")
    renewal_date = prompt_until_valid(
        "Renewal date (YYYY-MM-DD): ", validate_date, today=current_date
    )
    free_trial = prompt_until_valid(
        "Free trial? (yes/no): ", validate_yes_no
    )
    data = load_data(data_path)
    add_subscription(data, name, renewal_date, free_trial, current_date)
    save_data(data, data_path)
    print("Subscription added!\n------------------")


def view_cli(data_path=DATA_FILE):
    print("------------------\nSUBSCRIPTIONS\n")
    print_subscriptions(load_data(data_path)["Subscriptions"])
    print("------------------")


def edit_cli(data_path=DATA_FILE):
    data = load_data(data_path)
    subscriptions = data["Subscriptions"]
    if not subscriptions:
        print("No subscriptions found!\n------------------")
        return

    print("------------------\nEDIT SUBSCRIPTION\n")
    print_subscriptions(subscriptions, with_id=True)
    subscription_id = prompt_for_id(subscriptions)
    current = find_subscription(subscriptions, subscription_id)
    print("Press Enter if you wish to leave the value unchanged")
    name = prompt_until_valid(
        f"Name [{current['name']}]: ", validate_optional_name
    )
    renewal_date = prompt_until_valid(
        f"Renewal Date [{current['renewal_date']}]: ",
        validate_date,
        today=date.today(),
        allow_empty=True,
    )
    current_trial = "yes" if current["free_trial"] else "no"
    free_trial = prompt_until_valid(
        f"Free trial? (yes/no) [{current_trial}]: ",
        validate_yes_no,
        allow_empty=True,
    )
    edit_subscription(data, subscription_id, name, renewal_date, free_trial)
    save_data(data, data_path)
    print("Subscription edited!\n------------------")


def validate_optional_name(value):
    if not value.strip():
        return None
    return validate_name(value)


def delete_cli(data_path=DATA_FILE):
    data = load_data(data_path)
    subscriptions = data["Subscriptions"]
    if not subscriptions:
        print("No subscriptions found!\n------------------")
        return

    print("------------------\nDELETE SUBSCRIPTION\n")
    print_subscriptions(subscriptions, with_id=True)
    subscription_id = prompt_for_id(subscriptions)
    delete_subscription(data, subscription_id)
    save_data(data, data_path)
    print("Subscription deleted!\n------------------")


def prompt_for_menu_choice():
    while True:
        try:
            choice = int(input("Enter number (1-5): "))
            if 1 <= choice <= 5:
                return choice
            print("Value must be a number from 1 to 5.")
        except ValueError:
            print("Number must be an integer.")


def main(data_path=DATA_FILE):
    try:
        load_data(data_path)
    except StorageError as error:
        sys.exit(f"Could not start SubTrack: {error}")

    actions = {1: add_cli, 2: view_cli, 3: edit_cli, 4: delete_cli}
    while True:
        print(
            "SUBSCRIPTIONS TRACKER\n\n"
            "1. Add a new subscription\n"
            "2. View all subscriptions\n"
            "3. Edit a subscription\n"
            "4. Delete a subscription\n"
            "5. Exit"
        )
        choice = prompt_for_menu_choice()
        if choice == 5:
            sys.exit("Bye!")
        try:
            actions[choice](data_path)
        except StorageError as error:
            print(f"Storage error: {error}")


if __name__ == "__main__":
    main()
