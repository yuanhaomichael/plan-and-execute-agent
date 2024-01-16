from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain.llms import OpenAI

from lib.check_env import is_local

from source.models.google_email_details import GoogleEmailDetails
from source.services.credentials_manager import CredentialsManager
from source.tools.google_email.email_details_definer import EmailDetailsDefiner

from email.mime.text import MIMEText
import base64


class GoogleEmailTool():
    name = "google_email_tool"
    description = """
               Useful for managing emails. Tasks include drafting and retrieving emails.
               You should enter the full user task query, that user entered before.
               Output is the email object or a success message for draft.
               """
    user_id = ""
    
    def __init__(self, user_id: str, **data):
        self.user_id = user_id

    def get_email_service(self, creds):
        return build("gmail", "v1", credentials=creds)

    def get_email_details(self, user_task: str, sender_email: str):
        definer = EmailDetailsDefiner()
        email_details = definer.define_email_details(user_task, sender_email)
        return email_details

    def draft_email(self, email_details: GoogleEmailDetails, sender_email:str):
        creds_manager = CredentialsManager()
        creds = creds_manager.get_creds(user_id=self.user_id, is_local=is_local())
        service = self.get_email_service(creds=creds)
        print("email_details", email_details)

        # Create a MIMEText object to represent the email
        email_msg = MIMEText(email_details['text'])
        email_msg['to'] = email_details['receiver']
        email_msg['from'] = email_details['sender'] or sender_email
        email_msg['subject'] = email_details['subject']
        
        # Base64 encode the email
        b64_bytes = base64.urlsafe_b64encode(email_msg.as_bytes())
        b64_string = b64_bytes.decode()
        
        # Prepare the body dictionary for the API call
        body = {
            'raw': b64_string
        }

        try:
            # Send the email
            message = service.users().messages().send(userId=sender_email, body=body).execute()
            print(f'Message Id: {message["id"]}')
            return message
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
        
    def summarize(self, emails):
        llm = OpenAI()
        return llm.predict(f"""You are a delightful assistant. Summarize email data below in a briefing. 
                           Do not ask follow up questions. If no emails, 
                           say you don't have emails: {str(emails)}""")

    def retrieve_emails(self, user_task: str, sender_email:str):
        creds_manager = CredentialsManager()
        creds = creds_manager.get_creds(user_id=self.user_id, is_local=is_local())
        service = self.get_email_service(creds=creds)

        try:
            results = service.users().messages().list(userId=sender_email).execute()
            messages = results.get('messages', [])
            emails = []
            for m in messages:
                msg_id = m['id']
                email = service.users().messages().get(userId=sender_email, id=msg_id).execute()
                email = self.decode_email(email)
                emails.append(email)

            print(emails)
            return self.summarize(emails[0:5])
        
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
        
    def decode_email(self, message: dict):
        # Get headers from the payload
        headers = message.get('payload', {}).get('headers', [])
        
        # Initialize fields with empty string in case the fields are not found
        subject, sender, receiver = '', '', ''
        
        # Loop through headers to get subject, sender, and receiver
        for header in headers:
            name = header.get('name', '').lower()
            if name == 'subject':
                subject = header.get('value', '')
            elif name == 'from':
                sender = header.get('value', '')
            elif name == 'to':
                receiver = header.get('value', '')

        # Get snippet
        snippet = message.get('snippet', '')
        
        # Get and decode email text data from base64 to utf-8
        data_encoded = message.get('payload', {}).get('body', {}).get('data', '')
        data_decoded = base64.urlsafe_b64decode(data_encoded).decode('utf-8', errors='ignore')

        # Form a dictionary with the required fields
        email_decoded = {
            'subject': subject,
            'sender': sender,
            'receiver': receiver,
            'snippet': snippet,
            'data': data_decoded
        }
        
        return email_decoded
