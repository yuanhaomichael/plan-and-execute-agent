from source.core.orchestration import Orchestration

# internal function for handler.start_jarvis
def start_jarvis_internal(user_request=None, user_id="j3UUgwYnu7NE1COPSjqp1dahv2g1", status="local", request_payload={}):
    # for local testing
    if user_request is None:
        user_request = input("What do you want to do?: ")

    orc = Orchestration()
    output = orc.plan_and_execute(user_request=user_request, user_id=user_id, status=status, request_payload=request_payload)

    return output


##################################
# Sample request_payload object
#
# request_payload = {
#     "last_executed_task": last_executed_task,
#     "all_tasks": all_tasks,
#     "body": body,
#     "body_type": body_type,
#     "created_at": created_at,
#     "mentions": mentions,
#     "sender": sender
# }