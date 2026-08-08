# SubTrack
### Video Demo: https://youtu.be/D8mAIBzS-7w

### Description
SubTrack is software where you can add your digital subscriptions and keep them organized in one place, making sure you never forget about a renewal or a forgotten active subscription. It is coded entirely in Python. Application logic and the command-line interface live in `project.py`, while JSON file handling lives in `storage.py`. Local subscriptions are stored in the ignored `data.json` file.

### `project.py`
`project.py` contains the validation, subscription operations, and command-line interface. The main function runs a menu that provides: 1) Add a new subscription 2) View existing subscriptions 3) Edit a subscription 4) Delete a subscription 5) Exit. On startup, `storage.py` creates `data.json` beside the application files if it does not exist.

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

### Dependencies and tests
The application uses only the Python standard library, so it has no runtime dependency file. Install `pytest` as a development dependency to run the tests:

```text
python -m pytest
```

### `test_project.py`
This file uses pytest to test validation, adding, editing, deleting, stable ID generation, legacy-data normalization, and JSON storage behavior. Storage tests use pytest temporary directories and never touch the user's real `data.json`.
