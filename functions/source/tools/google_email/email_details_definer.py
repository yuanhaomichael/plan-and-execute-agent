from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate
from source.models.google_email_details import GoogleEmailDetails

from langchain.output_parsers import PydanticOutputParser
from source.tools.gpt import GPT
from lib.get_env import safe_get_env

PROMPT_PREFIX = """
Your goal is to define email details based on user request or task. Draft the text for 
the email based on user context.
The email details should always include subject, sender, receiver, and text fields.
Return email in json format with details from user task:

JSON format:
{
  "subject": "Meeting Reminder",
  "sender": "john.doe@example.com",
  "receiver": "jane.doe@example.com",
  "text": "Dear Jane, This is a reminder for our meeting scheduled tomorrow at 10:30 AM. \n Best, John"
}

Examples:
"""

class EmailDetailsDefiner:
    
    def define_email_details(self, params):
        prompt = PROMPT_PREFIX + self.get_llm_examples()
        
        template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=prompt),
                HumanMessagePromptTemplate.from_template("{text}")
            ]
        )
        
        llm = GPT().model_dumb
        text = params['user_task'] + "\n" + params['user_context']
        model_response = llm(template.format_messages(text=text))

        parser = PydanticOutputParser(pydantic_object=GoogleEmailDetails)
        content = parser.parse(model_response.content)
        email_details_dict = {
            "subject": content.subject,
            "sender": content.sender,
            "receiver": content.receiver,
            "text": content.text
        }
        
        
        return email_details_dict
    
    def get_llm_examples(self):
        return """
**Example 1:**
User request: Send an email to Sarah about the "Project Update" meeting tomorrow at 10:30 AM. My email is john.doe@example.com and Sarah's email is sarah.smith@example.com.

Answer:
{
  "subject": "Project Update Meeting",
  "sender": "john.doe@example.com",
  "receiver": "sarah.smith@example.com",
  "text": "Dear Sarah,\n\nThis is a reminder for our Project Update meeting scheduled tomorrow at 10:30 AM.\n\nBest regards,\nJohn"
}

**Example 2:**
User request: Send a thank you email to David for the successful project completion. My email is mike@example.com and David's email is david.jones@example.com.

Answer:
{
  "subject": "Thank You",
  "sender": "mike@example.com",
  "receiver": "david.jones@example.com",
  "text": "Dear David,\n\nThank you for your hard work and dedication in completing the project successfully.\n\nBest regards,\nMike"
}

**Example 3:**
User request: Send an email to Lisa regarding the budget review meeting next Monday at 2:45 PM. My email is alex@example.com and Lisa's email is lisa.jones@example.com.

Answer:
{
  "subject": "Budget Review Meeting",
  "sender": "alex@example.com",
  "receiver": "lisa.jones@example.com",
  "text": "Dear Lisa,\n\nThis is to inform you about the Budget Review meeting scheduled for next Monday at 2:45 PM.\n\nBest regards,\nAlex"
}

... (and so on)
"""
