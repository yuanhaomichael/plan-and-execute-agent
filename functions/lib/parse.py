import re
import json

def parse_from_pattern_wrapper(input_string, wrapper_start, wrapper_end):
    pattern = re.escape(wrapper_start) + r'(.*?)' + re.escape(wrapper_end)

    matches = re.findall(pattern, input_string, re.DOTALL)

    if matches:
        return matches[0]
    else:
        return None
    

# can only be used for non-nested json
def parse_json_in_string(text):
    json_regex = r'\{[^\{]*?\}'
    
    json_matches = re.findall(json_regex, text, re.DOTALL)

    json_objects = []
    for match in json_matches:
        try:
            json_obj = json.loads(match)
            json_objects.append(json_obj)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError for match {match}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for match {match}: {e}")

    return json_objects[0]

