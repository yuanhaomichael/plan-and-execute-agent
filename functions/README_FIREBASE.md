Note: must be in the functions/folder

The venv is different one from the venv in the root folder for the python API

* python3.11 -m venv venv
* source venv/bin/activate
* python3.11 -m pip install -r requirements.txt
* firebase emulators:start --only functions
* firebase deploy --only functions
* firebase deploy --only functions:relay_new_message_event
* firebase emulators:start --only functions:relay_new_message_event
