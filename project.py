import sys
from datetime import date, datetime
from pathlib import Path
import json


#Main Menu
def main():
    check_json_existence()
    while True:
        print("SUBSCRIPTIONS TRACKER\n\n1.Add a new subscription\n2.View all subscriptions\n" \
        "3.Edit a subscription\n4.Delete a subscription\n5.Exit")
        while True:
            try:
                choice = int(input("Enter number(1-5): "))
                match choice:
                    case 1 | 2 | 3 | 4:
                        break
                    case 5:
                        sys.exit("Bye!")
                    case _:
                        print("Value must be number 1-5")
                        continue
            except ValueError:
                print("Number must be integer")
                continue
        match choice:
            case 1:
                add_sub()
            case 2:
                view_subs()
            case 3:
                edit_subs()
            case 4:
                delete_subs()



#Adding new subscription
def add_sub():
    print("------------------\nADD SUBSCRIPTION\n")
    name = input("Name: ").strip()
    current_date = f"{date.today():%Y-%m-%d}"
    print(f"Current date: {current_date}")
    renewal_date = check_date("Renewal date (YYYY-MM-DD): ", False)
    free_trial = check_yes_no("Free trial?(yes/no): ", False)
    with open("data.json", "r+") as file:
        data = json.load(file)
        data["Subscriptions"].append({"id": len(data["Subscriptions"])+1, "name": name, "date_of_addition": current_date, "renewal_date": renewal_date, "free_trial": free_trial})
        file.seek(0)
        json.dump(data, file, indent=4)
    print("Subscription added!\n------------------")


#Viewing all existing subscriptions
def view_subs():
    print("------------------\nSUBSCRIPTIONS\n")
    data = read_json()
    print_data(False, data)
    print("------------------")



#Edit existing subscription
def edit_subs():
    data = read_json()
    if len(data["Subscriptions"]) != 0:
        print("------------------\nEDIT SUBSCRIPTION\n")
        print_data(True, data)
        key = get_id(data)
        current_data = data["Subscriptions"][key-1]
        print("Press Enter if you wish to leave the value unchanged")
        new_name = input(f"Name [{current_data["name"]}]: ").strip()
        if new_name == "":
            new_name = current_data["name"]
        new_renewal = check_date(f"Renewal Date [{current_data["renewal_date"]}]: ", True)
        if new_renewal is None:
            new_renewal = current_data["renewal_date"]
        new_free_trial = check_yes_no(f"Free trial?(yes/no) [{current_data["free_trial"]}]: ", True)
        if new_free_trial is None:
            new_free_trial = current_data["free_trial"]
        data["Subscriptions"][key-1]["name"], data["Subscriptions"][key-1]["renewal_date"], data["Subscriptions"][key-1]["free_trial"] = new_name, new_renewal, new_free_trial
        with open("data.json", "w") as file:
            json.dump(data, file, indent=4)
        print("Subscription edited!\n------------------")
    else:
        print("No subscriptions found!\n------------------")



#Delete existing subscription
def delete_subs():
    data = read_json()
    if len(data["Subscriptions"]) != 0:
        print("------------------\nDELETE SUBSCRIPTION\n")
        print_data(True, data)
        key = get_id(data)
        for sub in data["Subscriptions"]:
            if sub["id"] > key:
                sub["id"] -= 1
        data["Subscriptions"].pop(key-1)
        with open("data.json", "w") as file:
            json.dump(data, file, indent=4)
        print("Subscription deleted!\n------------------")
    else:
        print("No subscriptions found!\n------------------")




#Checking if date format of user's input is correct
def check_date(s, new):
    while True:
        text = input(s).strip()
        if new and text == "":
            return None
        try:
            mydate = datetime.strptime(text, "%Y-%m-%d")
            dif = date(mydate.year, mydate.month, mydate.day) - date.today()
            if dif.days <= 0:
                print("Renewal date cannot be today or in the past.")
                continue
            return f"{mydate:%Y-%m-%d}"
        except ValueError:
            print("Incorrect date format.")
            continue


#Validity checker for the free_trial variable
def check_yes_no(s, new):
    while True:
        text = input(s).strip().lower()
        if new and text == "":
            return None
        if text in ["yes", "no"]:
            return text
        print("Value must be either yes or no")



#Read the file
def read_json():
    with open("data.json", "r") as file:
        return json.load(file)



#Print the file on screen for the user | bool: with_id | dict: data
def print_data(with_id, data):
    for sub in data["Subscriptions"]:
        if with_id:
            print(f"ID: {sub["id"]}, Name: {sub["name"]} | Date of Addition: {sub["date_of_addition"]} | Renewal Date: {sub["renewal_date"]} | Free Trial: {sub["free_trial"]}")
        else:
            print(f"Name: {sub["name"]} | Date of Addition: {sub["date_of_addition"]} | Renewal Date: {sub["renewal_date"]} | Free Trial: {sub["free_trial"]}")


#Get the subscription's id by the user
def get_id(data):
    while True:
        try:
            key = int(input("Enter ID: "))
            if key > 0 and key <= len(data["Subscriptions"]):
                return key
            print("Invalid ID")
        except ValueError:
            print("Key must be integer")
            continue


#Checking if json exists and if not adding the initial data
def check_json_existence():
    if not Path("data.json").exists():
        with open("data.json", "w") as file:
            json.dump({"Subscriptions": []}, file, indent=4)



if __name__ == "__main__":
    main()
