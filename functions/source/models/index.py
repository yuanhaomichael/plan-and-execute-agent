from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Attendee(BaseModel):
    email: Optional[str]
    name: Optional[str]
    displayName: Optional[str]


class GoogleCalendarCreate(BaseModel):
    summary: str = Field(description="A short summary of the event.", default="")
    location: str = Field(description="The location where the event will take place.", default="")
    description: str = Field(description="A detailed description of the event.", default="")
    start_date: str = Field(description="The date and time when the event starts.", default="")
    end_date: str = Field(description="The date and time when the event ends.", default="")
    calendar_id: str = Field(description="The ID of the calendar that the event is associated with.", default="")
    attendees: List[Dict] = Field(description="A list of name and email addresses of the people who are invited to the event.", default=[])
    time_zone: str = Field(description="The time zone of the user.",
                           default="America/Los_Angeles")

    class Config:
        arbitrary_types_allowed = True

    def attendees_google_format(self):
        attendees = []

        for email, name in self.attendees:
            attendees.append(
                {
                    "email": email,
                    "displayName": name
                }
            )

        return attendees



class GoogleCalendarUpdate(BaseModel):
    summary: str = Field(description="A short summary of the event.", default="")
    location: str = Field(description="The location where the event will take place.", default="")
    description: str = Field(description="A detailed description of the event.", default="")
    start_date: str = Field(description="The date and time when the event starts.", default="")
    end_date: str = Field(description="The date and time when the event ends.", default="")
    calendar_id: str = Field(description="The ID of the calendar that the event is associated with.", default="")
    attendees: List[Dict] = Field(description="A list of the email addresses of the people who are invited to the event.", default=[])
    time_zone: str = Field(description="The time zone of the user.",
                           default="America/Los_Angeles")
    event_id: str = Field(description="event ID referring to the event to update", default="")
    

    class Config:
        arbitrary_types_allowed = True

    def attendees_google_format(self):
        attendees = []

        for item in self.attendees:
            if "name" in item and "email" in item:
                attendees.append(
                    {
                        "email": item["email"],
                        "displayName": item["name"]
                    }
                )

        return attendees




class GoogleCalendarDelete(BaseModel):
    event_id: str = Field(description="Event ID", default="")
    calendar_id: str = Field(description="The ID of the calendar that the event is associated with.", default="")

    class Config:
        arbitrary_types_allowed = True



class GoogleCalendarRetrieveAndSummarize(BaseModel):
    user_task: str = Field(description="User's task request", default="")
    calendar_id: str = Field(description="The ID of the calendar that the event is associated with.", default="")

    class Config:
        arbitrary_types_allowed = True


class GoogleCalendarFind(BaseModel):
    user_task: str = Field(description="User's task request", default="")
    calendar_id: str = Field(description="The ID of the calendar that the event is associated with.", default="")



class GoogleEmailDetails(BaseModel):
    subject: str = Field(description="The subject of the email.")
    sender: str = Field(description="The email address of the sender.")
    receiver: str = Field(description="The email address of the receiver.")
    text: str = Field(description="The text content of the email.")

    class Config:
        arbitrary_types_allowed = True

