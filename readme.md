# SubTrack
### Video Demo: https://youtu.be/D8mAIBzS-7w

### Description
SubTrack is a software where you can add your digital subscriptions and keep them organized in one place, making sure you never forget about a renewal or a forgotten active subscription. It is coded entirely in python, and the project contains 5 files in total: `project.py`, `test_project.py`, `requirements.txt`, `data.json` and `README.md` (the one you are reading right now!).

### `project.py`
`project.py` contains all the functions required for the program to run. The main function of it is a constant loop of the main menu, which gives access to the features of the program which are: 1) Add a new subscription 2) View your existing subscriptions 3) Edit an existing subscription 4) Delete an existing subscription 5) Exit the program. The main function also calls the check_json_existence function which checks whether the data.json (the file containing all the subscriptions the user adds) exists, and if it doesn't it sets it up. In the main menu, the program waits for the user's input after printing the menu of choices, checks whether the input is an integer from 1-5 and then launches the corresponding feature.

### Adding a Subscription
If the user wants to add a subscription (number 1 in the main menu), the program asks for the name, autofills the date of addition, the renewal date (which checks if it has a correct format and if it is a future date through a check_date function) and whether it's a free trial or not (which checks if the user inputs either the word "yes" or "no", case-insensitive). The information is then written to `data.json` and the main menu reappears.

### Viewing Subscriptions
In case the user requests to view all his existing subscriptions by inputting the number 2 in the main menu, they are all printed line by line in the command line directly from the JSON file.

### Editing Subscriptions
If the user chooses to edit a subscription (number 3 in the main menu), the subscriptions are printed on screen but this time with their unique ID which the user is prompted to enter to edit the corresponding entry (user's input on IDs is checked for validity). The corresponding entry's data are reappeared one by one (name, renewal date and free trial | date of addition cannot be altered) with their previous value next to them. The user has the chance to just press enter and leave the value same as before or fill in a new value to alter the entry accordingly.

### Deleting Subscriptions
If the user chooses to delete a subscription (number 4 in the main menu), the program follows the same logic as before with the ID checking and the corresponding entry is deleted.

###  Exiting the Program
Choosing number 5 in the menu exits the program with a "Bye!" message.

### `requirements.txt`
This file is empty. No external libraries were used except the ones already installed with python: sys, datetime, pathlib and json.

### `test_project.py`
This file implements test functions using pytest for 3 of the functions of the main program: `check_date()` (which is used to check whether the format of the date the user inputs is correct), `check_yes_no()` (which is used to check whether the user has inputted a correct format of the word "yes" or the word "no") and `get_id()` (which is used to check whether the user has inputted a correct ID of the entry he wishes to edit or delete). Pytest's "monkeypatch" is used because these 3 functions require user input, and this tool provides it automatically for the sake of testing. The test_project.py file contains 2 functions for testing the `check_date()` function (one for regular input and one for the case where an empty input is allowed in the editing feature), 2 functions for testing the `check_yes_no()` function (similarly as the check_date function) and 1 function for testing the `get_id()` function. Additionally, a function named provide_iterable_elements is used which takes as an input "monkeypatch" and a list of items and returns back to each test function these items as iterable inputs as a replacement for the user's input.
