import boto3
import json

iot = boto3.client('iot')

def lambda_handler(event, context):
    response = iot.list_things()
    things = response['things']
    
    device_list = []
    for thing in things:
        details = iot.describe_thing(thingName=thing['thingName'])
        version = details.get('attributes', {}).get('firmwareVersion', 'Unknown')
        device_list.append({
            'device_name': thing['thingName'],
            'current_version': version
        })
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        },
        'body': json.dumps(device_list)
    }
