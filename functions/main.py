from firebase_functions.firestore_fn import (
  Event,
  Change,
  DocumentSnapshot,
)
from firebase_functions import firestore_fn, https_fn, options
from firebase_admin import initialize_app, firestore, credentials, auth

from source.core.start_jarvis import start_jarvis_internal
from source.services.credentials_manager import CredentialsManager
from source.tools.google_calendar.google_calendar_tool import GoogleCalendarTool

from googleapiclient.discovery import build

import json
import requests
import uuid
import traceback
from deepdiff import DeepDiff

from datetime import datetime, timedelta



cred = credentials.ApplicationDefault()
app = initialize_app()


@firestore_fn.on_document_updated(document="chats/{userId}", timeout_sec=60, memory=options.MemoryOption.GB_1)
def relay_new_message_event(event: Event[Change[DocumentSnapshot]]) -> None:
  API_URL = "https://run-jarvis-3bskt57j2q-uc.a.run.app"
  params = event.params
  userId = params['userId']
  old_obj = event.data.before.to_dict()
  new_obj = event.data.after.to_dict()
  print(f"params: {params}")

  if "messages" not in new_obj:
     return None
  
  old_messages = old_obj["messages"] if "messages" in old_obj else []
  new_messages = new_obj["messages"] if "messages" in new_obj else []
  print(f"old messages list length: {len(old_messages)}, new messages list length: {len(new_messages)}")
  
  difference = DeepDiff(old_messages, new_messages, ignore_order=True)
  # no need to call run_jarvis if only chat status changes
  if not difference and old_obj.get("status") == "ready" and new_obj.get("status") == "loading":
      return None


  input_data = None
  if len(new_messages) > 0:
    input_data = new_messages[-1]
  else:
     return None

  if input_data.get("status") == "task_creation":
    print(f"observed 'messages' field change in userId: {userId}, calling AWS lambda API for task creation...")
    
    body = {
        'text': input_data.get('text', None),
        'user_id': userId,
        'status': input_data.get('status', None),
        'last_executed_task': input_data.get('last_executed_task', None),
        'all_tasks': input_data.get('all_tasks', []),
        'body': input_data.get('body', {}),
        'body_type': input_data.get('body_type', None),
        'created_at': input_data.get('created_at', None),
        'mentions': input_data.get('mentions', []),
        'sender': input_data.get('sender', None),
        'id': input_data.get('id')
    }

    print(f"[BODY]: {str(body)}")
    # send API request to AWS Lambda function for AI processing

    try:
        # send API request to AWS Lambda function for AI processing
        response = requests.post(API_URL, json=body)

        # Print the response or handle the results
        print(response.status_code)
        print(response.text)
        
    except requests.RequestException as e:
        # handle any type of request exception
        print(f"Error sending the request: {e}")

    except Exception as e:
        # general exception handling
        print(f"An unexpected error occurred: {e}")


  elif input_data.get("status") == "execution":
    print(f"observed 'messages' field change in userId: {userId}, calling AWS lambda API for execution...")

    body = {
        'text': input_data.get('text', None),
        'user_id': userId,
        'status': input_data.get('status', None),
        'last_executed_task': input_data.get('last_executed_task', None),
        'all_tasks': input_data.get('all_tasks', []),
        'body': input_data.get('body', {}),
        'body_type': input_data.get('body_type', None),
        'created_at': input_data.get('created_at', None),
        'mentions': input_data.get('mentions', []),
        'sender': input_data.get('sender', None),
        'id': input_data.get('id')
    }

    print(f"[BODY]: {str(body)}")

    try:
        # send API request to AWS Lambda function for AI processing
        response = requests.post(API_URL, json=body)

        # Print the response or handle the results
        print(response.status_code)
        print(response.text)
        
    except requests.RequestException as e:
        # handle any type of request exception
        print(f"Error sending the request: {e}")

    except Exception as e:
        # general exception handling
        print(f"An unexpected error occurred: {e}")





def create_contact_profile(name, email, avatarURL=None, index=None):
    # Create a contact profile dictionary with a unique ID and optional username
    contact_profile = {
        'name': name,
        'email': email,
        'avatarURL': avatarURL if avatarURL else ''
    }
       
    return contact_profile


@firestore_fn.on_document_created(document="users/{userId}", timeout_sec=60, memory=options.MemoryOption.GB_1)
def fetch_user_contacts(event: Event[Change[DocumentSnapshot]]) -> None:
    # google auth, get user creds
    params = event.params
    user_id = params['userId']

    db = firestore.client()
    user_record = db.collection("users").document(user_id).get()
        
    if user_record.exists:
        user_record = user_record.to_dict()
        print(f"[USER RECORD]: {user_record}\n")
    else:
        print("No user record or credentials found.")

    # Check if access and refresh tokens are available for the user
    calendar_id = user_record.get("email")
    creds = CredentialsManager().get_creds(user_id=user_id)
    
    calendar_service = build('calendar', 'v3', credentials=creds)
    people_service = build('people', 'v1', credentials=creds, static_discovery=False)

    # get all event attendees
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    three_months_ago = (datetime.utcnow() - timedelta(days=90)).isoformat() + 'Z'

    events = GoogleCalendarTool(user_id=user_id).get_events_in_date_range(calendar=calendar_service, calendar_id=calendar_id, start_date=three_months_ago, end_date=now)
    attendees = []
    for event in events:
        if 'attendees' in event:
            for attendee in event['attendees']:
                # Check if the attendee is not the organizer and if a response has been received
                if not attendee.get('organizer', False) and attendee.get('responseStatus', 'needsAction') != 'needsAction':
                    email = attendee.get('email')
                    attendee_info = {
                        'email': email,
                        'displayName': attendee.get('displayName', email.split('@')[0]),
                        'responseStatus': attendee.get('responseStatus')
                    }
                    attendees.append(attendee_info)

    # get all email contacts
    people_result = people_service.people().connections().list(resourceName='people/me', pageSize=100,
                                                         personFields='names,emailAddresses').execute()
    contacts = people_result.get('connections', [])


    # Create a combined contacts list with profiles
    profile_list = []
    for index, attendee in enumerate(attendees):
        email = attendee['email']
        profile = create_contact_profile(
            name=attendee.get('displayName', email.split('@')[0]),
            email=email,
            index=index
        )
        profile_list.append(profile)

    for index, contact in enumerate(contacts, start=len(profile_list)):
        names = contact.get('names', [])
        emails = contact.get('emailAddresses', [])
        if names and emails:
            email = emails[0].get('value')
            profile = create_contact_profile(
                name=names[0].get('displayName', email.split('@')[0]),
                email=emails[0].get('value'),
                index=index
            )
            profile_list.append(profile)

    # deduplicate
    unique_profiles = {}
    for profile in profile_list:
        email = profile['email']
        if email not in unique_profiles:
            unique_profiles[email] = profile

    profile_list = list(unique_profiles.values())
    for index, profile in enumerate(profile_list):
        profile['id'] = str(uuid.uuid4()) 
        profile['username'] = f"{profile['name'].replace(' ', '')}" 
   

    # Write the profile list to Firestore
    profiles_ref = db.collection('profiles').document(user_id)
    profiles_ref.set({'profiles': profile_list}, merge=True)

    print(f'Updated profiles document for user_id: {user_id}')




@https_fn.on_request()
def test_cloud_new_message_trigger(req: https_fn.Request) -> https_fn.Response:
  input_data = req.get_json(force=True, silent=True)
  if not input_data:
     return https_fn.Response("No input data", status=200)
  mode = input_data.get("mode")
  user_id = input_data.get("user_id")

  print(input_data, mode, user_id)

  db = firestore.client()

  if mode == "task_creation":
    print("mode task creation")
    # add a new task_creation message
    task = {
      "text": "Meet with john at 9pm",
      "user_id": user_id,
      "status": "task_creation",
      "created_at": "2023-10-24T21:53:40Z",
      "mentions": [],
      "sender": "user",
      "id": str(uuid.uuid4())
    }
    chat_record = db.collection("chats").document(user_id).get()
    print(str(chat_record.to_dict()))
    tmp =  chat_record.to_dict()
    arr = []
    if 'messages' in tmp and tmp['messages']:
      arr =  tmp['messages']
    else:
      arr = []
    if chat_record.exists:
      arr.append(task)
      db.collection("chats").document(user_id).update({
          "messages": arr
      })
    else: 
        raise Exception("chat record does not exist")
  else:
    # change the last message's status field to "execution" and sender field to "system"
    print("mode execution")
    chat_ref = db.collection("chats").document(user_id)
    chat = chat_ref.get()

    if chat.exists:
        messages = chat.to_dict().get("messages", [])
        
        if messages:
            # Modify the last message's fields
            messages[-1]["status"] = "execution"
            messages[-1]["sender"] = "system"
            
            # Update the chat document with the modified messages
            chat_ref.update({
                "messages": messages
            })
        else:
            print("No messages found for the user.")
    else:
        print("Chat document does not exist for the user.")

  return https_fn.Response("good", status=200)





@https_fn.on_request()
def run_jarvis(req: https_fn.Request) -> https_fn.Response:
    try:
        input_data = req.get_json(force=True, silent=True)
    except json.JSONDecodeError:
        return https_fn.Response(json.dumps({"message": "Invalid JSON input"}), status=400)

    if not input_data:
        return https_fn.Response(json.dumps({"message": "input is empty"}), status=400)
    
    print(f"[INPUT_DATA]: {str(input_data)}")
    user_request = input_data.get('text', None)
    user_id = input_data.get('user_id', None)
    status = input_data.get('status', None) # "task creation" | "execution"
    last_executed_task = input_data.get('last_executed_task', None)
    all_tasks = input_data.get('all_tasks', [])
    body = input_data.get('body', {})
    body_type = input_data.get('body_type', None)
    created_at = input_data.get('created_at', None)
    mentions = input_data.get('mentions', [])
    sender = input_data.get('sender', None)
    id = input_data.get('id') # message id

    request_payload = {
        "last_executed_task": last_executed_task,
        "all_tasks": all_tasks if all_tasks else [],
        "body": body if body else {},
        "body_type": body_type,
        "created_at": created_at,
        "mentions": mentions if mentions else [],
        "sender": sender
    }
    print(f"[REQUEST_PAYLOAD]: {str(request_payload)}")


    # change status to loading
    db = firestore.client()
    chat_ref = db.collection("chats").document(user_id)
    chat = chat_ref.get()

    if chat.exists:
        chat_ref.update({"status": "loading"})
    else:
        print("Updating chat status but chat document does not exist for the user.")


    # begin processing
    output = {}
    try:
        raw_output = start_jarvis_internal(user_id=user_id, user_request=user_request, status=status, request_payload=request_payload)

        # if status is confirmation, 
        # add fields all_tasks, last_executed_task, body, body_type, status
        if raw_output.get("status") == "confirmation":
           print("CONFIRMATION")
           output = {
              **input_data,
              "text": raw_output.get("text", "Ok!"),
              "all_tasks": raw_output.get("all_tasks", []),
              "last_executed_task": raw_output.get("last_executed_task"),
              "body": raw_output.get("body"),
              "body_type": raw_output.get("body_type"),
              "status": "confirmation",
              "sender": "system",
              # for confirmation, create a new item in messages list, so we add an id field
              "id": str(uuid.uuid4())
           }
           if "user_id" in output:
              output.pop("user_id")

        # if status is success or failure, keep things unchanged
        elif raw_output.get("status") == "success" or raw_output.get("status") == "failure":
           print("SUCCESS/FAILURE")
           output = {
              **input_data,
              "text": raw_output.get("text", "Ok!"),
              "status": raw_output.get("status")
           }
           if "user_id" in output:
              output.pop("user_id")

        print(f"[API OUTPUT]: {str(output)}")

        # write to DB
        if chat.exists:
            messages = chat.to_dict().get("messages")
            
            if messages:
                if status == "task_creation":
                    # add a new message and store the output
                    messages.append(output)
                elif status == "execution":
                    for index, message in enumerate(messages):
                        if message.get('id') == id:
                            messages[index] = output
                            break
                
                chat_ref.update({"status": "ready", "messages": messages})
            else:
                print("No messages found for the user.")
        else:
            print("Updating message status but chat document does not exist for the user.")

        status_code = 200
    except Exception as e:
        stack_trace = traceback.format_exc()  # Capture the stack trace
        
        output = {
            **output,
            "status": "failure",
            "error_message": str(e),
            "stack_trace": stack_trace
        }
        status_code = 500
    finally:
        return https_fn.Response(json.dumps(output), status=status_code)
