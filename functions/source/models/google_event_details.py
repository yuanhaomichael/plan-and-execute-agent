from pydantic import BaseModel, Field
from typing import List


class GoogleEventDetails(BaseModel):
    summary: str = Field(description="A short summary of the event.")
    location: str = Field(description="The location where the event will take place.")
    description: str = Field(description="A detailed description of the event.")
    start_date: str = Field(description="The date and time when the event starts.")
    end_date: str = Field(description="The date and time when the event ends.")
    calendar_id: str = Field(description="The ID of the calendar that the event is associated with.")
    attendees: List[str] = Field(description="A list of the email addresses of the people who are invited to the event.")
    time_zone: str = Field(description="The time zone of the user.",
                           default="America/Los_Angeles")

    class Config:
        arbitrary_types_allowed = True

    def attendees_google_format(self):
        attendees = []

        for email in self.attendees:
            attendees.append(
                {
                    "email": email
                }
            )

        return attendees
