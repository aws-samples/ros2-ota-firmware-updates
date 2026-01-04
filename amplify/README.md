# ROS2 OTA Firmware Update Web Application

## Overview
This project is a web application for performing over-the-air firmware updates for ROS2 devices, built using React and AWS Amplify Gen2.

## Prerequisites
- Node.js (version 20.18.1)
- AWS CLI configured with appropriate credentials

## Deployment Instructions

### 1. Deploy Infrastructure
Deploy the AWS infrastructure (CodeCommit repository and Amplify app) using CDK:

```bash
# Navigate to the infrastructure directory
cd infrastructure

# Install dependencies
npm install

# Bootstrap the CDK stack
npx aws-cdk bootstrap

# Deploy the CDK stack
npx aws-cdk deploy
```

The deployment will:
1. Create a CodeCommit repository
2. Automatically populate it with the Amplify project contents
3. Set up an Amplify app connected to the repository
4. Configure automatic builds

Note the output from the CDK deployment:
- `RepositoryCloneUrlHttp`: The CodeCommit repository URL
- `AmplifyAppId`: The Amplify application ID

### 2. Access Your Application
Once the deployment is complete, you can access your application through the Amplify console. The URL will be available in the Amplify Console under "Domain Management". You can also access the application using the URL provided in the output of the CDK deployment. The `ROS2OTAAmplifyStack.AmplifyAppDefaultDomain` output will contain the URL.

### 3. Adding Users to the Authorized Group

After deploying your application, you'll need to add users to the authorized Cognito group to grant them access. Use the provided script:

1. First, get your Cognito User Pool ID from the AWS Console or the Amplify CLI output
2. Run the add_user_to_group.sh script with your username and user pool ID:

```bash
cd src
./add_user_to_group.sh -u <username> -p <user-pool-id>
```

For example: `./add_user_to_group.sh -u john.doe@example.com -p us-east-1_abc123xyz`

This will add the specified user to the "ROS-OTA-AuthorizedUsers" group, granting them access to manage firmware updates through the web application.

## Infrastructure Details

The CDK stack creates:
1. AWS CodeCommit repository to host your code
2. Lambda function to populate the repository with your application code
3. AWS Amplify application configured for automatic deployments
4. Main branch with auto-build enabled
5. Single-page application redirects

## Cleaning Up Resources

To remove all deployed resources:

```bash
# Delete the Amplify app and CodeCommit repository
cd infrastructure
npx aws-cdk destroy
```

