import boto3
import json

BUCKET_NAME = 'jarvis-ai-dev'
s3 = boto3.client('s3', region_name='us-east-1')

def write_to_s3(user_id, data):
    object_key = f'{user_id}.json'
    json_data = json.dumps(data)
    try:
        s3.put_object(Bucket=BUCKET_NAME, Key=object_key, Body=json_data)
        print(f'Successfully uploaded {object_key} to {BUCKET_NAME}')
    except Exception as e:
        print(f'Failed to upload {object_key} to {BUCKET_NAME}: {e}')

def get_from_s3(user_id):
    object_key = f'{user_id}.json'
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=object_key)
        json_data = response['Body'].read().decode('utf-8')
        return json.loads(json_data)
    except Exception as e:
        print(f'Failed to retrieve {object_key} from {BUCKET_NAME}: {e}')
