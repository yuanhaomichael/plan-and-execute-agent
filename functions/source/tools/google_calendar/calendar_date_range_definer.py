import json

from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate
from source.tools.gpt import GPT
from lib.parse import parse_json_in_string

PROMPT_PREFIX = """
Your goal is to define a date range based on the user task. 
The user's current date and time and time zone are provided in the user context, so you must
provide convert the date range you defined to UTC time based on user's timezone.

return in JSON format:
{
  "min_date": "2023-09-15T00:00:00-08:00",
  "max_date": "2023-09-15T23:59:59-08:00"
}

"""


class DateRangeDefiner:
    
    def define_date_range(self, text: str, user_context):
        user_context_str = f"""
            timezone: {user_context.get("time_zone")}
            current date and time:{user_context.get("current_date_and_time")}
            Examples: 
            {self.get_llm_examples()}
            """
        prompt = PROMPT_PREFIX + user_context_str

        template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=prompt),
                HumanMessagePromptTemplate.from_template("User task: {text}"),
            ]
        )

        llm = GPT().model_dumb
        model_response = llm(template.format_messages(text=[text]))
        print(parse_json_in_string(model_response.content))

        try:
            date_range_dict = parse_json_in_string(model_response.content)
            print(f"DATE RANGE: {str(date_range_dict)}")
            return date_range_dict
        except json.JSONDecodeError as json_err:
            # Handle JSON decode error
            raise ValueError(f"Failed to decode JSON: {json_err}")
        except Exception as e:
            # Optionally, catch all other exceptions
            raise RuntimeError(f"An unexpected error occurred: {e}")


    def get_llm_examples(self):
        return """
\nExamples:

**Example 1:**
User request: give me my gcal events today

User context: 
{
    "today_date": "2023-09-14",
    "current_time": "08:00:00",
    "time_zone": "America/Los_Angeles"
};

Answer:
{
  "min_date": "2023-09-14T00:00:00-08:00",
  "max_date": "2023-09-14T23:59:59-08:00"
}

**Example 2:**
User request: show me my schedule for next week

Environment context: 
{
    "today_date": "2023-09-14",
    "current_time": "08:00:00",
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "min_date": "2023-09-18T00:00:00-08:00",
  "max_date": "2023-09-24T23:59:59-08:00"
}

**Example 3:**
User request: what's on my calendar for this weekend

Environment context: 
{
    "today_date": "2023-09-14",
    "current_time": "08:00:00",
    "local_time_zone": "America/Los_Angeles"
};

Answer:
{
  "min_date": "2023-09-16T00:00:00-08:00",
  "max_date": "2023-09-17T23:59:59-08:00"
}

"""


