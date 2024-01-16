import datetime
import pytz
from typing import Literal
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain.llms import OpenAI

from lib.search import full_text_search
from lib.check_env import is_local

from source.models.index import GoogleCalendarFind
from source.models.index import GoogleCalendarUpdate
from source.models.index import GoogleCalendarDelete
from source.models.index import GoogleCalendarCreate
from source.models.index import GoogleCalendarRetrieveAndSummarize

from source.services.credentials_manager import CredentialsManager
from source.services.user_context_provider import UserContextProvider
from source.tools.google_calendar.event_details_definer import EventDetailsDefiner
from source.tools.google_calendar.calendar_date_range_definer import DateRangeDefiner
from source.tools.gpt import GPT


class GoogleCalendarTool():
    name = "google_calendar_tool"
    description = """
               Useful for managing google calendar. For tasks like creating, deleting, updating events.
               You should enter full user task query, that user entered before.  
               Output is the link url to the created event.
               """
    user_id = ""
    calendar_id = ""
    user_context = {}
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        user_context = UserContextProvider(user_id=user_id).get_user_context(mentions=[])
        self.calendar_id = user_context.get("calendar_id")
        self.user_context = user_context


    def get_calendar(self, creds):
        calendar = build("calendar", "v3", credentials=creds)
        return calendar

    def find_event(self, params: GoogleCalendarFind, mode=None): 
        creds_manager = CredentialsManager()
        creds = creds_manager.get_creds(user_id=self.user_id, is_local=is_local())
        calendar = self.get_calendar(creds=creds)


        events = self.get_all_events(calendar, calendar_id=params.calendar_id)
        matched_events = full_text_search(search_keyword=params.user_task, entities=events, search_fields=['summary'], limit=1)

        if matched_events is None or len(matched_events) == 0:
            return {}
        matched_event = matched_events[0] if len(matched_events) > 0 else None
        if not matched_event:
            return {}
        else:
            return {
                "event_id": matched_event.get('id', None),
                "summary": matched_event.get('summary', None),
                'start_date': matched_event.get('start', {}).get('dateTime', None),
                'end_date': matched_event.get('end', {}).get('dateTime', None)
            } 

    def create_event(self, params: GoogleCalendarCreate, mode: Literal["confirmation", "execution"]):
        
        confirmation_params = dict(params)
        attendees = confirmation_params['attendees']
        attendees_formatted = []
        for item in attendees:
            formatted_item = dict(item)
            if 'displayName' in formatted_item:
                formatted_item['name'] = formatted_item['displayName']
            if 'email' not in formatted_item or len(formatted_item['email']) == 0:
                continue
                
            attendees_formatted.append(formatted_item)

        confirmation_params['attendees'] = attendees_formatted

        if mode == "confirmation":
            return confirmation_params
        
        creds_manager = CredentialsManager()
        creds = creds_manager.get_creds(user_id=self.user_id, is_local=is_local())
        calendar = self.get_calendar(creds=creds)

        event = {
            'summary': params.summary,
            'location': params.location,
            'description': params.description,
            'start': {
                'dateTime': params.start_date,
                'timeZone': params.time_zone,
            },
            'end': {
                'dateTime': params.end_date,
                'timeZone': params.time_zone,
            },
            'recurrence': [],
            'attendees': params.attendees,
            'reminders': {
                'useDefault': True,
            },
        }

        try:
            event = calendar.events().insert(calendarId=params.calendar_id, body=event).execute()

        except HttpError as error:
            print("An error occurred:", error)

        return event
    
    def update_event(self, params: GoogleCalendarUpdate, mode: Literal["confirmation", "execution"]):
        confirmation_params = dict(params)
        attendees = confirmation_params['attendees']
        attendees_formatted = []
        for item in attendees:
            formatted_item = dict(item)
            if 'displayName' in formatted_item:
                formatted_item['name'] = formatted_item['displayName']
            attendees_formatted.append(formatted_item)

        confirmation_params['attendees'] = attendees_formatted

        if mode == "confirmation":
            return confirmation_params

        
        creds_manager = CredentialsManager()
        creds = creds_manager.get_creds(user_id=self.user_id, is_local=is_local())
        calendar = self.get_calendar(creds=creds)

        event = calendar.events().get(calendarId=params.calendar_id, eventId=params.event_id).execute()
        event['location'] = params.location
        event['description'] = params.description
        event['start'] = {
            'dateTime': params.start_date,
            'timeZone': params.time_zone,
        }
        event['end'] = {
            'dateTime': params.end_date,
            'timeZone': params.time_zone,
        }
        event['attendees'] = params.attendees

        
        try:
            updated_event = calendar.events().update(calendarId=params.calendar_id, eventId=params.event_id, body=event).execute()
        except HttpError as error:
            print("An error occurred:", error)
            return None

        return updated_event

    def delete_event(self, params: GoogleCalendarDelete, mode: Literal["confirmation", "execution"]):
        creds_manager = CredentialsManager()
        creds = creds_manager.get_creds(user_id=self.user_id, is_local=is_local())
        calendar = self.get_calendar(creds=creds)

        event = self.find_event_by_id(calendar, params.event_id, params.calendar_id)

        if mode == "confirmation":
            return {
                "event_id": params.event_id,
                "summary": event.get('summary', None),
                'start_date': event.get('start', {}).get('dateTime', None),
                'end_date': event.get('end', {}).get('dateTime', None),
                "time_zone": self.user_context.get("time_zone"),
                "calendar_id": self.calendar_id
            } 

        try:
            calendar.events().delete(calendarId=params.calendar_id, eventId=params.event_id).execute()
        except HttpError as error:
            print(f"An error occurred: {error}")

        return {
            "event_id": params.event_id,
            "summary": event.get('summary', None),
            'start_date': event.get('start', {}).get('dateTime', None),
            'end_date': event.get('end', {}).get('dateTime', None),
            "time_zone": self.user_context.get("time_zone"),
            "calendar_id": self.calendar_id
        } 
    
    def retrieve_and_summarize_events(self, params: GoogleCalendarRetrieveAndSummarize, mode=None):
        creds_manager = CredentialsManager()
        creds = creds_manager.get_creds(user_id=self.user_id, is_local=is_local())
        calendar = self.get_calendar(creds=creds)

        date_range = DateRangeDefiner().define_date_range(params.user_task, user_context=self.user_context)
        print(date_range)
        events = self.get_events_in_date_range(calendar=calendar, calendar_id=params.calendar_id, start_date=date_range['min_date'], end_date=date_range['max_date'])
        events = self.parse_events(events)

        print(events)
        return {
            "calendar_id": self.calendar_id,
            "_text": self.summarize(events)
        }
    
    def parse_events(self, events_list):
        parsed_events = []
        for event in events_list:
            # Extracting the datetime and summary info from each event
            start_time = event['start']['dateTime']
            end_time = event['end']['dateTime']
            summary = event.get('summary', '')  # Use an empty string if summary is not present

            # Creating a dictionary with the required info and appending it to the result list
            parsed_events.append({
                'start': start_time,
                'end': end_time,
                'summary': summary
            })
        
        return parsed_events
    
    def summarize(self, events):
        llm = GPT().model_dumb
        prompt = f"""You are a delightful assistant, be fun, easygoing, and concise. 
                    Below is a person's schedule. Respond as if talking directly
                    to the person to give a briefing about his or her schedule.

                    If no events, say there are no events.
                    Events:
                    {str(events)}"""

        return llm.predict(prompt)
    
    def get_events_in_date_range(self, calendar, calendar_id: str, start_date: str, end_date: str):
        # Parse input date strings to datetime objects
        start_datetime = parse(start_date)
        end_datetime = parse(end_date)

        time_min = start_datetime.astimezone(pytz.UTC).isoformat()
        time_max = end_datetime.astimezone(pytz.UTC).isoformat()

        all_events = []
        page_token = None
        while True:
            events = calendar.events().list(
                calendarId=calendar_id, 
                maxResults=50, 
                timeMax=time_max, 
                timeMin=time_min, 
                pageToken=page_token
            ).execute()

            for event in events['items']:
                all_events.append(event)

            page_token = events.get('nextPageToken')
            if not page_token:
                break
        
        return all_events
    
    def get_all_events(self, calendar, calendar_id: str):
        now = datetime.datetime.utcnow()
        time_min = (now - datetime.timedelta(days=1)).isoformat() + 'Z'  # 'Z' indicates UTC time
        time_max = (now + relativedelta(months=1)).isoformat() + 'Z'

        all_events = []
        page_token = None
        while True:
            events = calendar.events().list(calendarId=calendar_id, maxResults=50, timeMax=time_max, timeMin=time_min, pageToken=page_token).execute()
            for event in events['items']:
                all_events.append(event)
            page_token = events.get('nextPageToken')
            if not page_token:
                break
        
        return all_events

    def get_event_details(self, user_task: str):
        definer = EventDetailsDefiner()
        event_details = definer.define_event_details(user_task)

        return event_details

    def find_event_by_id(self, calendar, event_id: str, calendar_id: str):
        event = calendar.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return event

