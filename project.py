import sys
from datetime import date
from pathlib import Path

from storage import StorageError, load_data, save_data
from subscriptions import (
    UPCOMING_DAYS,
    add_subscription,
    delete_subscription,
    edit_subscription,
    find_subscription,
    get_renewal_groups,
    mark_subscription_renewed,
    validate_currency,
    validate_date,
    validate_name,
    validate_optional_name,
    validate_renewal_price,
    validate_yes_no,
)


DATA_FILE = Path(__file__).with_name("data.json")


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


def prompt_for_new_price():
    while True:
        text = input("Next renewal price (blank if unknown): ").strip()
        if not text:
            return None, None
        try:
            price = validate_renewal_price(text)
            currency = prompt_until_valid(
                "Currency (for example EUR): ", validate_currency
            )
            return price, currency
        except ValueError as error:
            print(error)


def prompt_for_edited_price(current):
    current_price = current["renewal_price"]
    current_currency = current["currency"]
    shown_price = (
        f"{current_price} {current_currency}"
        if current_price is not None
        else "not provided"
    )

    while True:
        text = input(
            f"Next renewal price [{shown_price}] "
            "(Enter keeps it, 'none' removes it): "
        ).strip()
        if not text:
            return False, None, None
        if text.lower() == "none":
            return True, None, None
        try:
            price = validate_renewal_price(text)
            break
        except ValueError as error:
            print(error)

    while True:
        prompt = "Currency (for example EUR): "
        if current_currency is not None:
            prompt = f"Currency [{current_currency}]: "
        text = input(prompt).strip()
        if not text and current_currency is not None:
            return True, price, current_currency
        try:
            return True, price, validate_currency(text)
        except ValueError as error:
            print(error)


def renewal_status(subscription, today=None):
    current_date = today if today is not None else date.today()
    renewal_date = date.fromisoformat(subscription["renewal_date"])
    days_until = (renewal_date - current_date).days
    if days_until < 0:
        days_overdue = abs(days_until)
        suffix = "day" if days_overdue == 1 else "days"
        return f"Overdue by {days_overdue} {suffix}"
    if days_until == 0:
        return "Due today"
    suffix = "day" if days_until == 1 else "days"
    return f"In {days_until} {suffix}"


def format_price(subscription):
    if subscription["renewal_price"] is None:
        return "Not provided"
    return f"{subscription['renewal_price']} {subscription['currency']}"


def print_subscription_table(
    subscriptions, today=None, include_status=False, include_added=True
):
    if not subscriptions:
        return

    headers = ["ID", "Name", "Renewal", "Price", "Trial"]
    rows = []
    if include_added:
        headers.insert(2, "Added")
    if include_status:
        status_position = 4 if include_added else 3
        headers.insert(status_position, "Status")

    for subscription in subscriptions:
        row = [
            str(subscription["id"]),
            subscription["name"],
            subscription["renewal_date"],
            format_price(subscription),
            "FREE TRIAL" if subscription["free_trial"] else "No",
        ]
        if include_added:
            row.insert(2, subscription["date_of_addition"])
        if include_status:
            status_position = 4 if include_added else 3
            row.insert(status_position, renewal_status(subscription, today))
        rows.append(row)

    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    formatted_headers = (
        header.ljust(widths[index]) for index, header in enumerate(headers)
    )
    print(" | ".join(formatted_headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def print_dashboard(data, today=None):
    subscriptions = data["Subscriptions"]
    print("\nSUBTRACK 1.0 - RENEWAL DASHBOARD")
    print("=" * 34)
    if not subscriptions:
        print("No subscriptions yet. Add one from the main menu.\n")
        return

    current_date = today if today is not None else date.today()
    groups = get_renewal_groups(subscriptions, current_date)
    headings = {
        "overdue": "OVERDUE",
        "due_today": "DUE TODAY",
        "upcoming": f"COMING UP IN THE NEXT {UPCOMING_DAYS} DAYS",
    }
    if not any(groups.values()):
        print(f"No renewals due in the next {UPCOMING_DAYS} days.\n")
        return

    for group_name, heading in headings.items():
        if groups[group_name]:
            print(f"\n{heading}")
            print_subscription_table(
                groups[group_name],
                current_date,
                include_status=True,
                include_added=False,
            )
    print()


def add_cli(data_path=DATA_FILE):
    print("\nADD SUBSCRIPTION")
    name = prompt_until_valid("Name: ", validate_name)
    current_date = date.today()
    print(f"Current date: {current_date:%Y-%m-%d}")
    renewal_date = prompt_until_valid(
        "Renewal date (YYYY-MM-DD): ", validate_date, today=current_date
    )
    free_trial = prompt_until_valid(
        "Free trial? (yes/no): ", validate_yes_no
    )
    renewal_price, currency = prompt_for_new_price()

    data = load_data(data_path)
    add_subscription(
        data,
        name,
        renewal_date,
        free_trial,
        current_date,
        renewal_price,
        currency,
    )
    save_data(data, data_path)
    print("Subscription added!\n")


def view_cli(data_path=DATA_FILE):
    data = load_data(data_path)
    subscriptions = data["Subscriptions"]
    print("\nALL SUBSCRIPTIONS")
    if not subscriptions:
        print("No subscriptions yet.\n")
        return
    print_subscription_table(subscriptions)
    print()


def upcoming_cli(data_path=DATA_FILE):
    print_dashboard(load_data(data_path))


def mark_renewed_cli(data_path=DATA_FILE):
    data = load_data(data_path)
    subscriptions = data["Subscriptions"]
    if not subscriptions:
        print("No subscriptions found.\n")
        return

    print("\nMARK SUBSCRIPTION AS RENEWED")
    print_subscription_table(
        subscriptions, include_status=True, include_added=False
    )
    subscription_id = prompt_for_id(subscriptions)
    next_date = prompt_until_valid(
        "Next renewal date (YYYY-MM-DD): ", validate_date, today=date.today()
    )
    renewed = mark_subscription_renewed(
        data, subscription_id, next_date, date.today()
    )
    save_data(data, data_path)
    print(f"{renewed['name']} marked as renewed.\n")


def edit_cli(data_path=DATA_FILE):
    data = load_data(data_path)
    subscriptions = data["Subscriptions"]
    if not subscriptions:
        print("No subscriptions found.\n")
        return

    print("\nEDIT SUBSCRIPTION")
    print_subscription_table(subscriptions)
    subscription_id = prompt_for_id(subscriptions)
    current = find_subscription(subscriptions, subscription_id)
    print("Press Enter to leave a value unchanged.")
    name = prompt_until_valid(
        f"Name [{current['name']}]: ", validate_optional_name
    )
    renewal_date = prompt_until_valid(
        f"Renewal date [{current['renewal_date']}]: ",
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
    change_price, renewal_price, currency = prompt_for_edited_price(current)

    edit_options = {
        "name": name,
        "renewal_date": renewal_date,
        "free_trial": free_trial,
        "today": date.today(),
    }
    if change_price:
        edit_options["renewal_price"] = renewal_price
        edit_options["currency"] = currency
    edit_subscription(data, subscription_id, **edit_options)
    save_data(data, data_path)
    print("Subscription edited!\n")


def delete_cli(data_path=DATA_FILE):
    data = load_data(data_path)
    subscriptions = data["Subscriptions"]
    if not subscriptions:
        print("No subscriptions found.\n")
        return

    print("\nDELETE SUBSCRIPTION")
    print_subscription_table(subscriptions)
    subscription_id = prompt_for_id(subscriptions)
    deleted = delete_subscription(data, subscription_id)
    save_data(data, data_path)
    print(f"{deleted['name']} deleted.\n")


def prompt_for_menu_choice():
    while True:
        try:
            choice = int(input("Enter number (1-7): "))
            if 1 <= choice <= 7:
                return choice
            print("Value must be a number from 1 to 7.")
        except ValueError:
            print("Number must be an integer.")


def print_menu():
    print(
        "SUBTRACK 1.0\n"
        "1. Add subscription\n"
        "2. View all subscriptions\n"
        "3. View upcoming renewals\n"
        "4. Mark subscription as renewed\n"
        "5. Edit subscription\n"
        "6. Delete subscription\n"
        "7. Exit"
    )


def main(data_path=DATA_FILE):
    try:
        data = load_data(data_path)
    except StorageError as error:
        sys.exit(f"Could not start SubTrack: {error}")

    print_dashboard(data)
    actions = {
        1: add_cli,
        2: view_cli,
        3: upcoming_cli,
        4: mark_renewed_cli,
        5: edit_cli,
        6: delete_cli,
    }
    while True:
        print_menu()
        choice = prompt_for_menu_choice()
        if choice == 7:
            sys.exit("Bye!")
        try:
            actions[choice](data_path)
        except StorageError as error:
            print(f"Storage error: {error}")


if __name__ == "__main__":
    main()
