import boto3
import json
import uuid

iot = boto3.client('iot')
sts = boto3.client('sts')

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    try:
        print("Event body:", event['body'])
        print(type(event['body']))
        # Double JSON decode to handle extra encoding layer
        if isinstance(event['body'], str):
            try:
                # First decode
                body = json.loads(event['body'])
                
                # Check if the result is still a string, indicating another layer
                if isinstance(body, str):
                    body = json.loads(body)  # Second decode
            except json.JSONDecodeError as e:
                print(f"JSON decoding error: {e}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    },
                    'body': json.dumps({'message': 'Invalid JSON format', 'error': str(e)})
                }
        else:
            body = event['body']  # If already a dictionary, use as-is

        device_name = body['device_name']
        version = body['new_version']
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            },
            'body': json.dumps({'message': 'Error occurred', 'error': str(e)})
        }
    account_id = sts.get_caller_identity()["Account"]
    
    job_id = str(uuid.uuid4())
    target = f"arn:aws:iot:us-east-1:{account_id}:thing/{device_name}"
    
    job_document = {
        "operation": "Deploy-ROS-Firmware",
        "jobDocument": {
            "thingName": device_name,
            "attributeUpdate": {
                "attributes": {
                    "firmwareVersion": version
                }
            }
        },
        "version": version
    }
    
    try:
        # Create a job to update the firmware
        response = iot.create_job(
            jobId=job_id,
            targets=[target],
            document=json.dumps(job_document),
            targetSelection='SNAPSHOT',
            description=f"Firmware update to version {version}",
        )
        # Check the response's status code to ensure success
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("Job created successfully:", response)
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                },
                'body': json.dumps({'message': 'Job created successfully:', 'response': response})
            }
        else:
            # If the create_job response indicates failure
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                },
                'body': json.dumps({'message': 'Failed to create job', 'response': response})
            }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            },
            'body': json.dumps({'message': 'Internal Server Error', 'error': str(e)})
        }
    