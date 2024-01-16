from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import PromptTemplate

from source.tools.google_calendar.event_details_definer import EventDetailsDefiner
from source.tools.google_email.email_details_definer import EmailDetailsDefiner
from source.tools.google_calendar.google_calendar_tool import GoogleCalendarTool
from source.tools.search import SearchTool
from source.tools.google_email.google_email_tool import GoogleEmailTool
from source.tools.companion import Companion

from source.models.index import GoogleCalendarFind
from source.models.index import GoogleCalendarUpdate
from source.models.index import GoogleCalendarDelete
from source.models.index import GoogleCalendarCreate
from source.models.index import GoogleCalendarRetrieveAndSummarize

from source.services.user_context_provider import UserContextProvider
from source.tools.gpt import GPT

import datetime
import json
import uuid
from lib.parse import parse_from_pattern_wrapper
from lib.get_env import safe_get_env

# Get current date and time
now = datetime.datetime.now()
current_date_time = now.strftime('%Y-%m-%d %H:%M:%S')

USER_REQUEST_LIMIT = 500

class Orchestration:
    def plan_and_execute(self, user_request: str, user_id: str, status: str, request_payload):
        # get user context including previous chat history and contacts 
        user_context = UserContextProvider(user_id=user_id).get_user_context(mentions=request_payload.get("mentions", []))
        print(f"[USER CONTEXT]: {str(user_context)}")

        # security: cut off limit for user request
        user_request = user_request[0:USER_REQUEST_LIMIT]

        # build up the api response object
        api_response = {}

        # declare the list of tools
        tools = {
            'event-details-definer': '',
            'calendar.create': '',
            'calendar.update': '',
            'calendar.retrieve_and_summarize': 'retrieve events based on user request and summarize',
            'calendar.find_one_event': 'find the closest event that match the user request',
            'calendar.delete': '',
            # 'email-details-definer': '',
            # 'email.find_one_email': '',
            # 'email.get_emails': '',
            # 'email.send': ''
            'companion.chat': 'chat with a friendly companion who can help brainstorm and have conversations'
        }

        # core AI pipeline: 
        # - "task_creation": starting plan & execute agent from the beginning
        # - "execution": resume a in-progress execute agent
        if status == "task_creation" or status == "execution" or status == "local":
            tasks_list = []

            # "task_creation": build task_list then execute
            if status == "task_creation" or status == "local":
                #########################################
                # 1. planner agent plans and return a list of tasks
                output_parser = CommaSeparatedListOutputParser()
                format_instructions = output_parser.get_format_instructions()
                planning_prompt = PromptTemplate(
                    template="""Given the tools below and user request: {user_request},
                    come up with tools to utilize, in sequential order, to achieve the user's request.

                    Instructions:
                    - only send email when the request specifically mentioned sending email
                    - to update a calendar event you must first find the old event and define new event details
                    ======\n
                    Tools: \n
                    {tools}.\n
                    ======\n
                    {format_instructions}
                    """,
                    input_variables=["tools", "user_request"],
                    partial_variables={"format_instructions": format_instructions}
                )

                _input = planning_prompt.format(tools=str(tools), user_request=user_request)
                output = GPT().model_smart.predict(_input)

                tasks_list = output_parser.parse(output)
                print(f"Here is the list of tasks: {str(tasks_list)}")

            # "execution": retrieve last_executed_task and task_list
            elif status == "execution":
                print("EXECUTION")
                last_executed_task = request_payload['last_executed_task']
                all_tasks = request_payload['all_tasks']
                print(last_executed_task, all_tasks)

                if last_executed_task in all_tasks and all_tasks.index(last_executed_task) != len(all_tasks) - 1:
                    start_index = all_tasks.index(last_executed_task) + 1
                    tasks_list = all_tasks[start_index:]
                else:
                    print(f"The last_executed_task {last_executed_task} is the final task in the list or not in the list at all.")
                    api_response = {
                        "text": "Sorry, I am unable to process your request.",
                        "user_id": user_id,
                        "status": "failure",
                        "last_executed_task": request_payload.get("last_executed_task"),
                        "all_tasks": request_payload.get("all_tasks"),
                        "body": request_payload.get('body', {}),
                        "body_type": request_payload.get('body_type'),
                        "created_at": self.get_current_time(),
                        "mentions": request_payload.get('mentions'),
                        "sender": "system"
                    }



            #########################################
            # 2. solver agent execute task one by one
            input_output_tuples = [] # track all input/output for each tool execution

            # if tool's required params is None, default to user task and user context as input
            body = request_payload.get("body", {})
            default_tool_input = { "user_task": user_request, "user_context": str(user_context), "calendar_id": user_context["calendar_id"], **body}

            # initialize and keep track of previous task output
            prev_task_output = default_tool_input
            
            for idx, task_tool in enumerate(tasks_list):
                # get all required params for the task tool
                params_model = self.get_params(task_tool=task_tool)
                if params_model:
                    params = params_model().dict()
                else:
                    params = None
                print(f"executing {task_tool}..., \n[REQUIRED PARAMS]: {str(params)}\n")
                print(f"[INPUT/OUTPUT TUPLES]: \n{str(input_output_tuples)}\n")

                # get tool
                tool_kit = self.get_tool(tool_name=task_tool, user_id=user_id)
                tool = tool_kit['tool']

                # check if the tool needs to get confirmation from user first
                if tool_kit['needs_confirmation'] and status != "local" and status != "execution":
                    mode = "confirmation"
                else: 
                    mode = "execution"


                # set prev task output
                if idx > 0:
                    prev_task_output = input_output_tuples[idx - 1][1]

                # tool execution
                if not params:
                    # by default, if task_tool requires no params, use default
                    input = {
                        **default_tool_input,
                        **prev_task_output
                    }
                    output = tool(input, mode)
                    print(f"[OUTPUT]: \n{output}\n")
                    input_output_tuples.append((input, output))
                else:
                    # format the data and output so far into params needed for the task_tool
                    raw_params_from_context = [(prev_task_output,{})] if len(input_output_tuples) == 0 else input_output_tuples

                    input = self.build_tool_input(raw_params_from_context, params)
                    print(f"[INPUT]: {str(input)} \n\n[PREV TASK OUTPUT]: {str(prev_task_output)}\n")

                    # execute tool
                    pydantic_formatted_input = params_model(**input)

                    output = tool(pydantic_formatted_input, mode)
                    input_output_tuples.append((input, output))
                    print(f"[OUTPUT]: \n{output}\n")

                # ===========================================
                # if mode is confirmation, break the loop now
                # and return confirmation body
                if mode == "confirmation" and status != "local":
                    api_response = { 
                        "body": {**output, "_text": ""}, 
                        "body_type": task_tool,
                        "status": "confirmation",
                        "text": "" if not output.get("_text") else output.get("_text"),
                        "last_executed_task": tasks_list[idx - 1] 
                            if len(tasks_list) > 1 else "dummy-tool",
                        "all_tasks": tasks_list
                    }
                    break
                if (mode == "execution" or status == "local") and idx == len(tasks_list) - 1:
                    api_response = { 
                        "body": {**output}, 
                        "body_type": task_tool,
                        "status": "success",
                        "text": "",
                        "last_executed_task": tasks_list[idx - 1] 
                            if len(tasks_list) > 1 else "dummy-tool",
                        "all_tasks": tasks_list
                    }

            # enrich api_response
            api_response = {
                "user_id": user_id,
                "created_at": self.get_current_time(),
                "mentions": request_payload.get("mentions", []),
                "sender": "system",
                **api_response
            }

        elif status == "declined":
            api_response = {
                "text": "Ok, sounds good.",
                "user_id": user_id,
                "status": "success",
                "last_executed_task": request_payload.get("last_executed_task"),
                "all_tasks": request_payload.get("all_tasks"),
                "body": request_payload.get("body", {}),
                "body_type": request_payload.get("body_type", ""),
                "created_at": self.get_current_time(),
                "mentions": [],
                "sender": "system"
            }

        api_response["body"]["id"] = str(uuid.uuid4())
        print(f"[RAW RESPONSE]: \n {str(api_response)}")
        return api_response


    def build_tool_input(self, raw_params, params_from_doc):
        params = {}
        
        for param_set in raw_params:
            for param_dict in param_set:
                for key, value in param_dict.items():
                    if key in params_from_doc and isinstance(value, type(params_from_doc[key])):
                        params[key] = value

        # Ensure that all required params are present
        for required_param, default_value in params_from_doc.items():
            required_type = type(default_value)
            if required_param not in params:
                raise ValueError(f"Required parameter {required_param} of type {required_type} not found in raw_params.")

        return params


    def get_tool(self, tool_name, user_id):
        calendar = GoogleCalendarTool(user_id=user_id)
        companion = Companion()
        # email = GoogleEmailTool(user_id=user_id)
        tools_map = {
            'event-details-definer': { "tool": EventDetailsDefiner().define_event_details, "needs_confirmation": False },
            'calendar.create': { "tool": calendar.create_event, "needs_confirmation": True },
            'calendar.update': { "tool": calendar.update_event, "needs_confirmation": True },
            'calendar.retrieve_and_summarize': { "tool": calendar.retrieve_and_summarize_events, "needs_confirmation": True },
            'calendar.find_one_event': { "tool": calendar.find_event, "needs_confirmation": False },
            'calendar.delete': { "tool": calendar.delete_event, "needs_confirmation": True },
            'companion.chat': { "tool": companion.chat, "needs_confirmation": True }
            # 'email-details-definer': { "tool": EmailDetailsDefiner().define_email_details, "needs_confirmation": False },
            # 'email.find_one_email': { "tool": email.find_one_email, "needs_confirmation": False },
            # 'email.retrieve': { "tool": email.retrieve_emails, "needs_confirmation": False },
            # 'email.send': { "tool": email.draft_email, "needs_confirmation": True }
        }

        if tool_name in tools_map:
            return tools_map[tool_name]
        return None
       
    def get_params(self, task_tool):
        params = {
            "event-details-definer": None,
            "calendar.create": GoogleCalendarCreate,
            "calendar.update": GoogleCalendarUpdate,
            "calendar.delete": GoogleCalendarDelete,
            "calendar.find_one_event": GoogleCalendarFind,
            "calendar.retrieve_and_summarize": GoogleCalendarRetrieveAndSummarize,
            'companion.chat': None
        }
        if task_tool in params:
            return params[task_tool]
        return None


    def get_current_time(self):
        current_time_utc = datetime.datetime.utcnow()
        formatted_time = current_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        return formatted_time