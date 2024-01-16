import boto3
from botocore.exceptions import ClientError
from typing import Union, Dict

session = boto3.session.Session()
dynamodb = session.resource('dynamodb', region_name='us-east-1')

table = dynamodb.Table('jarvis-ai-dev')

def get_record_by_key(key: str, key_name: str = "user_id") -> dict:
    try:
        response = table.get_item(Key={key_name: key})
    except ClientError as e:
        print(f"An error occurred: {e.response['Error']['Message']}")
        return None
    else:
        return response.get('Item', {})

def create_record(item: dict) -> dict:
    try:
        response = table.put_item(Item=item)
    except ClientError as e:
        print(f"An error occurred: {e.response['Error']['Message']}")
        return None
    else:
        return response



def construct_update_expression(update_fields: Union[Dict[str, str], list], mode: str = "set") -> (str, dict):
    if mode == "set":
        update_expression = "SET " + ", ".join(f"{field} = :{field}" for field in update_fields)
        expression_attribute_values = {f":{field}": value for field, value in update_fields.items()}
    elif mode == "delete":
        update_expression = "REMOVE " + ", ".join(field for field in update_fields)
        expression_attribute_values = {}  # No values needed for delete
    else:
        raise ValueError("Invalid mode. Use 'set' or 'delete'.")
    return update_expression, expression_attribute_values

def update_record_by_key(key: str, update_fields: Union[Dict[str, str], list], mode: str = "set", key_name = "user_id") -> dict:
    update_expression, expression_attribute_values = construct_update_expression(update_fields, mode)
    try:
        response = table.update_item(
            Key={key_name: key},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as e:
        print(f"An error occurred: {e.response['Error']['Message']}")
        return None
    else:
        return response

