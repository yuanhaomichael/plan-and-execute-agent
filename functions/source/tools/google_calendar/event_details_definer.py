import json

from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate

from source.tools.gpt import GPT

PROMPT_PREFIX = """
You goal is to define event details based on user task, user context, and previous calendar event details, if any.
Summary field should be always filled. Default to today if user didn't mention date.
Return event in json format with details from user task, user context, and prev event details:

JSON format:
{
  "summary": "Google I/O 2023",
  "location": "Mountain View, CA",
  "description": "The annual Google I/O conference",
  "start_date": "2023-09-15T10:30:00-08:00",
  "end_date": "2023-09-15T12:30:00-08:00",
  "calendar_id": "1234567890",
  "attendees": [{"email": "abc@gmail.com", "displayName": "Sarah Abc"}],
  "time_zone": "America/Los_Angeles"
}

"""


class EventDetailsDefiner:

    def define_event_details(self, params, mode=None):
        prompt = PROMPT_PREFIX

        template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=prompt),
                HumanMessagePromptTemplate.from_template("{text}"),
            ]
        )
        print(f"EVENT DETAILS PARAMS {str(params)}")
        llm = GPT().model_dumb
        text = f"""
            User context, task, and prev event (if any):
            {str(params)}
        """
        model_response = llm(template.format_messages(text=[text]))

        try:
            event_details_dict = json.loads(model_response.content)
            print("EVENT DETAILS", str(event_details_dict))
            return event_details_dict
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {e}")


    def get_llm_examples(self):
        return """
\nExamples:

**Example 1:**
User task: Create a project update meeting tomorrow with sarah at 10:30 AM for 2 hours.
User context, task, and prev event (if any):
{
    "email": "zakharazatian@gmail.com"
    "today_date": 2023/09/14,
    "current_time": 07:41:19,
    "calendar_id": "zakharazatian@gmail.com"
    "local_time_zone": "America/Los_Angeles"
    "contacts": {
       {
        "email": "sarah.smith@example.com",
        "name": "Sarah Smith",
       }
    }
};

Answer:
{
  "summary": "Project Update",
  "location": "",
  "description": "",
  "start_date": "2023-09-15T10:30:00-08:00",
  "end_date": "2023-09-15T12:30:00-08:00",
  "calendar_id": "zakharazatian@gmail.com",
  "attendees": [{"email": "sarah.smith@example.com", "displayName": "Sarah Smith"}],
  "time_zone": "America/Los_Angeles"
}

**Example 2: **
User context, task, and prev event (if any): 
{'user_task': 'Could you update meeting with Alex to 2 hours later', 'user_context': "{'name': 'Big Jarvis', 'email': 'ja5617131@gmail.com', 'calendar_id': 'ja5617131@gmail.com', 'today_date_and_time': '2023-10-26 11:26:59', 'local_time_zone': 'America/Los_Angeles', 'contacts': [], 'chat_history': []}", 'calendar_id': 'ja5617131@gmail.com', 'event_id': '375omjd0lnhafobb09tktvldhh', 'summary': 'Meet with Alex', 'start_date': '2023-10-27T13:00:00-07:00', 'end_date': '2023-10-27T13:45:00-07:00'}


Answer: 
{'summary': 'Meet with Alex', 'location': '', 'description': '', 'start_date': '2023-10-27T15:00:00-07:00', 'end_date': '2023-10-27T15:45:00-07:00', 'calendar_id': 'ja5617131@gmail.com', 'attendees': [], 'time_zone': 'America/Los_Angeles'}
"""


additional_examples = """
**Example 2:**
User request: Schedule a conference call with the team for "Weekly Status Meeting," this Friday at 3:00 PM for 1.5 hours. My email is manager@example.com.

User context:
{
    "email": "zakharazatian@gmail.com"
};
Environment context: 
{
    "today_date": 2023/09/14,
    "current_time": 08:00:00,
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "summary": "Weekly Status Meeting",
  "location": "",
  "description": "",
  "start_date": "2023-09-15T15:00:00-08:00",
  "end_date": "2023-09-15T16:30:00-08:00",
  "calendar_id": "manager@example.com",
  "attendees": [],
  "time_zone": "America/Los_Angeles"
}

**Example 3:**
User request: Create a meeting with Lisa titled "Budget Review," next Monday at 2:45 PM for 45 minutes. Lisa's email is lisa.jones@example.com. My email is alex@example.com.
User context:
{
    "email": "zakharazatian@gmail.com"
};
Environment context: 
{
    "today_date": 2023/09/14,
    "current_time": 08:00:00,
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "summary": "Budget Review",
  "location": "",
  "description": "",
  "start_date": "2023-09-18T14:45:00-08:00",
  "end_date": "2023-09-18T15:30:00-08:00",
  "calendar_id": "alex@example.com",
  "attendees": ["lisa.jones@example.com", "alex@example.com"],
  "time_zone": "America/Los_Angeles"
}


**Example 4:**
User request: Set up a team meeting for "Project Kickoff," next Wednesday at 9:00 AM for 2 hours. My email is project.manager@example.com.

User context:
{
    "email": "zakharazatian@gmail.com"
};
Environment context: 
{
    "today_date": 2023/09/14,
    "current_time": 08:00:00,
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "summary": "Project Kickoff",
  "location": "",
  "description": "",
  "start_date": "2023-09-20T09:00:00-08:00",
  "end_date": "2023-09-20T11:00:00-08:00",
  "calendar_id": "project.manager@example.com",
  "attendees": [],
  "time_zone": "America/Los_Angeles"
}

**Example 5:**
User request: Create an event with David called "Team Building," next Saturday at 11:30 AM for 3 hours. David's email is david.smith@example.com. My email is teamlead@example.com.

User context:
{
    "email": "zakharazatian@gmail.com"
};
Environment context: 
{
    "today_date": 2023/09/14,
    "current_time": 08:00:00,
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "summary": "Team Building",
  "location": "",
  "description": "",
  "start_date": "2023-09-23T11:30:00-08:00",
  "end_date": "2023-09-23T14:30:00-08:00",
  "calendar_id": "teamlead@example.com",
  "attendees": ["david.smith@example.com", "teamlead@example.com"],
  "time_zone": "America/Los_Angeles"
}

**Example 6:**
User request: Create event meeting with John called "Zakhar & John", today at 6 pm for 1 hour. John email is - zazman1999@gmail.com. My email is zakharazatian@gmail.com.

User context:
{
    "email": "zakharazatian@gmail.com"
};
Environment context: 
{
    "today_date": 2023/09/14,
    "current_time": 08:00:00,
    "local_time_zone": "America/Los_Angeles"
};

Answer: 
{
  "summary": "Zakhar & John",
  "location": "",
  "description": "",
  "start_date": "2023-09-14T18:00:00-08:00",
  "end_date": "2023-09-14T19:00:00-08:00",
  "calendar_id": "zakharazatian@gmail.com",
  "attendees": ["zazman1999@gmail.com", "zakharazatian@gmail.com"],
  "time_zone": "America/Los_Angeles"
}
"""


"""
**Example 1:**
User request:
Create a meeting with Sarah titled "Project Update," tomorrow at 10:30 AM for 2 hours in Cafe Barista. Sarah's email is sarah.smith@example.com. My email is john.doe@example.com.

User context:
{
    "email": "john.doe@example.com"
};
Environment context: 
{
    "today_date": "2023-09-14",
    "current_time": "07:41:19",
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "summary": "Project Update",
  "location": "Cafe Barista",
  "description": "",
  "start_date": "2023-09-15T10:30:00-08:00",
  "end_date": "2023-09-15T12:30:00-08:00",
  "calendar_id": "john.doe@example.com",
  "attendees": ["sarah.smith@example.com", "john.doe@example.com"],
  "time_zone": "America/Los_Angeles"
}

**Example 2:**
User request:
Schedule a conference call with the team for "Weekly Status Meeting," this Friday at 3:00 PM for 1.5 hours. My email is manager@example.com.

User context:
{
    "email": "manager@example.com"
};
Environment context: 
{
    "today_date": "2023-09-14",
    "current_time": "08:00:00",
    "local_time_zone": "America/Los_Angeles"
};

Answer:
```json
{
  "summary": "Weekly Status Meeting",
  "location": "",
  "description": "",
  "start_date": "2023-09-15T15:00:00-08:00",
  "end_date": "2023-09-15T16:30:00-08:00",
  "calendar_id": "manager@example.com",
  "attendees": [],
  "time_zone": "America/Los_Angeles"
}
```

**Example 3:**
User request:
Create a meeting with Lisa titled "Budget Review," next Monday at 2:45 PM for 45 minutes in Conference Room A. Lisa's email is lisa.jones@example.com. My email is alex@example.com.

User context:
{
    "email": "alex@example.com"
};
Environment context: 
{
    "today_date": "2023-09-14",
    "current_time": "08:00:00",
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "summary": "Budget Review",
  "location": "Conference Room A",
  "description": "",
  "start_date": "2023-09-18T14:45:00-08:00",
  "end_date": "2023-09-18T15:30:00-08:00",
  "calendar_id": "alex@example.com",
  "attendees": ["lisa.jones@example.com", "alex@example.com"],
  "time_zone": "America/Los_Angeles"
}

**Example 4:**
User request:
Set up a team meeting for "Project Kickoff," next Wednesday at 9:00 AM for 2 hours in Conference Room B. My email is project.manager@example.com.

User context:
{
    "email": "project.manager@example.com"
};
Environment context: 
{
    "today_date": "2023-09-14",
    "current_time": "08:00:00",
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "summary": "Project Kickoff",
  "location": "Conference Room B",
  "description": "",
  "start_date": "2023-09-20T09:00:00-08:00",
  "end_date": "2023-09-20T11:00:00-08:00",
  "calendar_id": "project.manager@example.com",
  "attendees": [],
  "time_zone": "America/Los_Angeles"
}

**Example 5:**
User request:
Create an event with David called "Team Building," next Saturday at 11:30 AM for 3 hours at Park Pavilion. David's email is david.smith@example.com. My email is teamlead@example.com.

User context:
{
    "email": "teamlead@example.com"
};
Environment context: 
{
    "today_date": "2023-09-14",
    "current_time": "08:00:00",
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "summary": "Team Building",
  "location": "Park Pavilion",
  "description": "",
  "start_date": "2023-09-23T11:30:00-08:00",
  "end_date": "2023-09-23T14:30:00-08:00",
  "calendar_id": "teamlead@example.com",
  "attendees": ["david.smith@example.com", "teamlead@example.com"],
  "time_zone": "America/Los_Angeles"
}

**Example 6:**
User request:
Create an event meeting with John called "Zakhar & John," today at 6 pm for 1 hour in Meeting Room 1. John's email is zazman1999@gmail.com. My email is zakharazatian@gmail.com.

User context:
{
    "email": "zakharazatian@gmail.com"
};
Environment context: 
{
    "today_date": "2023-09-14",
    "current_time": "08:00:00",
    "local_time_zone": "America/Los_Angeles"
};

Answer: 
{
  "summary": "Zakhar & John",
  "location": "Meeting Room 1",
  "description": "",
  "start_date": "2023-09-14T18:00:00-08:00",
  "end_date": "2023-09-14T19:00:00-08:00",
  "calendar_id": "zakharazatian@gmail.com",
  "attendees": ["zazman1999@gmail.com", "zakharazatian@gmail.com"],
  "time_zone": "America/Los_Angeles"
}

**Example 7:**
User request:
Create an event meeting with John called "Zakhar & John," today at 6 pm for 1 hour in Meeting Room 1. John's email is zazman1999@gmail.com.

User context:
{
    "email": "myemail@example.com"
};
Environment context: 
{
    "today_date": "2023-09-14",
    "current_time": "08:00:00",
    "local_time_zone": "America/Los_Angeles"
};

Answer: 
{
  "summary": "Zakhar & John",
  "location": "Meeting Room 1",
  "description": "",
  "start_date": "2023-09-14T18:00:00-08:00",
  "end_date": "2023-09-14T19:00:00-08:00",
  "calendar_id": "zakharazatian@gmail.com",
  "attendees": ["zazman1999@gmail.com", "myemail@example.com"],
  "time_zone": "America/Los_Angeles"
}

**Example 5:**
User request:
Create an event with David called "Team Building," next Saturday at 11:30 AM for 3 hours at Park Pavilion. David's email is david.smith@example.com.

User context:
{
    "email": "myemail2@gmail.com"
};
Environment context: 
{
    "today_date": "2023-09-14",
    "current_time": "08:00:00",
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "summary": "Team Building",
  "location": "Park Pavilion",
  "description": "",
  "start_date": "2023-09-23T11:30:00-08:00",
  "end_date": "2023-09-23T14:30:00-08:00",
  "calendar_id": "teamlead@example.com",
  "attendees": ["david.smith@example.com", "myemail2@gmail.com"],
  "time_zone": "America/Los_Angeles"
}
"""