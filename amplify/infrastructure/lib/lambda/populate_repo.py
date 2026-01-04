import os
import json
import time
import boto3
import shutil
import urllib3
import subprocess
from typing import Dict, Any
import zipfile

def run_command(command: str, cwd: str = None) -> str:
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(
            command.split(),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error: {str(e)}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise Exception(f"Command failed: {command}\nError: {str(e)}")

def send_cfn_response(event: Dict[str, Any], context: Any, response_status: str, reason: str = None, physical_resource_id: str = None):
    """Send a response to CloudFormation"""
    response_url = event.get('ResponseURL')
    if not response_url:
        print('No ResponseURL found in event')
        return
    
    print(f'Sending response to {response_url}')
    
    response_body = {
        'Status': response_status,
        'Reason': reason or 'See CloudWatch logs for details',
        'PhysicalResourceId': physical_resource_id or context.log_stream_name,
        'StackId': event.get('StackId'),
        'RequestId': event.get('RequestId'),
        'LogicalResourceId': event.get('LogicalResourceId'),
        'NoEcho': False,
    }
    
    try:
        http = urllib3.PoolManager()
        response = http.request(
            'PUT',
            response_url,
            body=json.dumps(response_body).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        print(f'CloudFormation response status code: {response.status}')
    except Exception as e:
        print(f'Failed to send CloudFormation response: {str(e)}')

def handler(event: Dict[str, Any], context: Any):
    """Lambda function handler"""
    print('Event:', json.dumps(event))
    
    try:
        # Get the source repository URL from GitHub
        source_repo_url = "https://github.com/aws-samples/ros2-ota-firmware-updates/archive/refs/heads/main.zip"
        
        if event.get('RequestType') in ['Create', 'Update']:
            print('Starting repository population process...')
            
            # Create temporary directories with unique names
            timestamp = str(int(time.time() * 1000))
            source_dir = f'/tmp/source_{timestamp}'
            amplify_dir = f'/tmp/amplify_{timestamp}'
            zip_path = f'/tmp/repo_{timestamp}.zip'
            
            try:
                print('Downloading repository...')
                http = urllib3.PoolManager()
                response = http.request('GET', source_repo_url)
                if response.status != 200:
                    raise Exception(f'Failed to download repository: HTTP {response.status}')
                
                with open(zip_path, 'wb') as f:
                    f.write(response.data)
                print('Repository downloaded successfully')
                
                print('Creating source directory...')
                os.makedirs(source_dir, exist_ok=True)
                
                print('Extracting files...')
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(source_dir)
                
                print('Creating amplify directory...')
                os.makedirs(amplify_dir, exist_ok=True)
                
                # Find the extracted directory
                extracted_dir = None
                for item in os.listdir(source_dir):
                    if os.path.isdir(os.path.join(source_dir, item)):
                        extracted_dir = os.path.join(source_dir, item)
                        break
                
                if not extracted_dir:
                    raise Exception('Could not find extracted directory')
                
                print('Copying amplify directory...')
                amplify_source = os.path.join(extracted_dir, 'amplify')
                if not os.path.exists(amplify_source):
                    raise Exception('Amplify directory not found in repository')
                
                shutil.copytree(amplify_source, amplify_dir, dirs_exist_ok=True)
                
                # Remove infrastructure directory if it exists
                infrastructure_dir = os.path.join(amplify_dir, 'infrastructure')
                if os.path.exists(infrastructure_dir):
                    shutil.rmtree(infrastructure_dir)
                
                print('Reading directory contents...')
                contents = os.listdir(amplify_dir)
                print('Amplify directory contents:', contents)
                
                print('Creating CodeCommit repository...')
                codecommit = boto3.client('codecommit')
                repo_name = event['ResourceProperties']['RepositoryName']
                
                try:
                    # Try to get the repository to see if it exists
                    codecommit.get_repository(repositoryName=repo_name)
                    print('Repository already exists')
                except codecommit.exceptions.RepositoryDoesNotExistException:
                    # Create the repository if it doesn't exist
                    codecommit.create_repository(
                        repositoryName=repo_name,
                        repositoryDescription='Amplify app repository'
                    )
                    print('Repository created successfully')
                
                print('Creating initial commit...')
                # Create a commit with all files
                put_files = []
                for root, dirs, files in os.walk(amplify_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        relative_path = os.path.relpath(full_path, amplify_dir)
                        put_files.append({
                            'filePath': relative_path,
                            'fileMode': 'NORMAL',
                            'fileContent': open(full_path, 'rb').read()
                        })

                response = codecommit.create_commit(
                    repositoryName=repo_name,
                    branchName='main',
                    authorName='Frank Olotu',
                    email='fraolotu@amazon.com',
                    commitMessage='Initial commit from CDK',
                    putFiles=put_files
                )                
                commit_id = response['commitId']
                print('Created commit:', commit_id)
                
                # Clean up
                print('Cleaning up temporary files...')
                shutil.rmtree(source_dir)
                shutil.rmtree(amplify_dir)
                os.remove(zip_path)
                
                print('Repository population completed successfully')
                send_cfn_response(event, context, 'SUCCESS')
                return
                
            except Exception as e:
                print('Error during repository population:', str(e))
                send_cfn_response(event, context, 'FAILED', reason=str(e))
                return
        
        elif event.get('RequestType') == 'Delete':
            print('Delete request - no action needed')
            send_cfn_response(event, context, 'SUCCESS')
            return
        
    except Exception as e:
        print('Error:', str(e))
        send_cfn_response(event, context, 'FAILED', reason=str(e))
        return
