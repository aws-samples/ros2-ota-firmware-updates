import { CfnOutput, Stack, StackProps, Duration, aws_iam } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import {
  AuthorizationType,
  Cors,
  LambdaIntegration,
  RestApi,
  CognitoUserPoolsAuthorizer,
} from 'aws-cdk-lib/aws-apigateway';
import * as cognito from 'aws-cdk-lib/aws-cognito';

export class LambdaStack extends Stack {
  public readonly apiId: string;
  public readonly identityPoolId: string;
  public readonly apiEndpoint: string;
  public readonly userPoolId: string;
  public readonly userPoolClientId: string;
  public readonly userPoolEndpoint: string;

  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const stackName = this.node.addr.substring(0, 8);

    // Define the Lambda function to list devices
    const listDevicesFunction = new lambda.Function(this, `ListDevicesFunction-${stackName}`, {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'list_devices.lambda_handler',
      code: lambda.Code.fromAsset('./amplify/custom-functions/listDevices'),
      functionName: `ListDevicesFunction-${stackName}`,
      description: 'Custom Lambda function to list devices, created using CDK',
      timeout: Duration.seconds(30),
      memorySize: 128,
    });

    // Attach IoT ListThings permission to the Lambda role
    listDevicesFunction.addToRolePolicy(
      new aws_iam.PolicyStatement({
        actions: ['iot:ListThings', 'iot:DescribeThing'],
        resources: ['*'],
      })
    );

    // Define the Lambda function to list firmware versions
    const listVersionsFunction = new lambda.Function(this, `ListVersionsFunction-${stackName}`, {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'list_versions.lambda_handler',
      code: lambda.Code.fromAsset('./amplify/custom-functions/listVersions'),
      functionName: `ListVersionsFunction-${stackName}`,
      description: 'Custom Lambda function to list firmware versions, created using CDK',
      timeout: Duration.seconds(30),
      memorySize: 128,
    });

    // Define the Lambda function to update devices
    const updateDevicesFunction = new lambda.Function(this, `UpdateDevicesFunction-${stackName}`, {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'update_device.lambda_handler',
      code: lambda.Code.fromAsset('./amplify/custom-functions/updateDevice'),
        functionName: `UpdateDevicesFunction-${stackName}`,
      description: 'Custom Lambda function to update devices, created using CDK',
      timeout: Duration.seconds(30),
      memorySize: 128,
    });

    // Attach permissions for the update devices Lambda function
    updateDevicesFunction.addToRolePolicy(
      new aws_iam.PolicyStatement({
        actions: ['iot:CreateJob', 'iot:UpdateThing', 'sts:GetCallerIdentity'],
        resources: ['*'],
      })
    );

    // Create Cognito User Pool
    const userPool = new cognito.UserPool(this, `MyUserPool-${stackName}`, {
        userPoolName: `MyUserPool-${stackName}`,
      selfSignUpEnabled: true,
      signInAliases: { email: true },
      autoVerify: { email: true },
      standardAttributes: {
        email: {
          required: true,
          mutable: true,
        },
      },
    });

    // Add User Pool Client
    const userPoolClient = new cognito.UserPoolClient(this, `MyUserPoolClient-${stackName}`, {
      userPool,
      generateSecret: false,
    });

    // Create Cognito Group for Authorized Users
    const authorizedUsersGroup = new cognito.CfnUserPoolGroup(this, `ROS-OTA-AuthorizedUsersGroup`, {
        userPoolId: userPool.userPoolId,
        groupName: `ROS-OTA-AuthorizedUsers`,
      });

    this.userPoolId = userPool.userPoolId;
    this.userPoolClientId = userPoolClient.userPoolClientId;
    this.userPoolEndpoint = `https://${this.userPoolId}.auth.${this.region}.amazoncognito.com`

    // Create Cognito Identity Pool and link User Pool
    const identityPool = new cognito.CfnIdentityPool(this, `MyIdentityPool-${stackName}`, {
      allowUnauthenticatedIdentities: false,
      cognitoIdentityProviders: [
        {
          providerName: userPool.userPoolProviderName,
          clientId: userPoolClient.userPoolClientId,
        },
      ],
        identityPoolName: `MyIdentityPool-${stackName}`,
    });

    // IAM Role for the Authorized Users group
    const groupIAMRole = new aws_iam.Role(this, `ROS-OTA-AuthorizedUsersGroupRole`, {
        roleName: `ROS-OTA-AuthorizedUsersGroupRole`,
        assumedBy: new aws_iam.FederatedPrincipal(
          'cognito-identity.amazonaws.com',
          {
            StringEquals: {
              'cognito-identity.amazonaws.com:aud': identityPool.ref,
            },
            'ForAnyValue:StringLike': {
              'cognito-identity.amazonaws.com:amr': 'authenticated',
            },
          },
          'sts:AssumeRoleWithWebIdentity'
        ),
      });

    // Export Identity Pool and Auth Role ARNs for Amplify to use
    this.identityPoolId = identityPool.ref;

    // Define API Gateway
    const api = new RestApi(this, `DeviceApi-${stackName}`, {
      restApiName: `Device Service`,
      description: 'API for managing IoT devices and firmware versions.',
      defaultCorsPreflightOptions: {
        allowOrigins: Cors.ALL_ORIGINS,
        allowMethods: Cors.ALL_METHODS,
        allowHeaders: [
          'Content-Type',
          'X-Amz-Date',
          'Authorization',
          'X-Api-Key',
          'X-Amz-Security-Token',
        ],
        allowCredentials: true,
      },
    });

    this.apiId = api.restApiId;

    groupIAMRole.addToPolicy(
        new aws_iam.PolicyStatement({
          actions: ['execute-api:Invoke'], // Allow access to API Gateway
          resources: [`arn:aws:execute-api:${this.region}:${this.account}:${this.apiId}/*`],
        })
      );

    // Attach the IAM Role to the Cognito Group
    authorizedUsersGroup.roleArn = groupIAMRole.roleArn;

    // associate both roles with the Identity Pool
    new cognito.CfnIdentityPoolRoleAttachment(this, 'IdentityPoolRoleAttachment', {
      identityPoolId: identityPool.ref,
      roles: {
        'authenticated': groupIAMRole.roleArn,
        // 'unauthenticated': unauthRole.roleArn,
      },
    });

    // Attach Cognito Authorizer to API Gateway
    const authorizer = new CognitoUserPoolsAuthorizer(this, `MyUserPoolAuthorizer-${stackName}`, {
      cognitoUserPools: [userPool],
    });

    // Add resources and methods to API Gateway
    const devices = api.root.addResource('devices');
    devices.addMethod('GET', new LambdaIntegration(listDevicesFunction), {
      authorizationType: AuthorizationType.COGNITO,
      authorizer,
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
      ],
    });

    const versions = api.root.addResource('versions');
    versions.addMethod('GET', new LambdaIntegration(listVersionsFunction), {
      authorizationType: AuthorizationType.COGNITO,
      authorizer,
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
      ],
    });

    const updateDevice = api.root.addResource('update-device');
    updateDevice.addMethod(
      'POST',
      new LambdaIntegration(updateDevicesFunction),
      {
        authorizationType: AuthorizationType.COGNITO,
        authorizer,
        methodResponses: [
            {
              statusCode: '200',
              responseParameters: {
                'method.response.header.Access-Control-Allow-Origin': true,
              },
            },
          ],
      }
    );

    this.apiEndpoint = api.url;

    // Output relevant information
    new CfnOutput(this, 'ApiId', {
      value: this.apiId,
      description: 'API Gateway ID',
    });

    new CfnOutput(this, 'ApiEndpoint', {
      value: this.apiEndpoint,
      description: 'API Gateway URL',
    });

    new CfnOutput(this, 'CognitoUserPoolId', {
      value: this.userPoolId,
      description: 'Cognito User Pool ID',
    });

    new CfnOutput(this, 'CognitoUserPoolClientId', {
        value: this.userPoolClientId,
        description: 'Cognito User Pool Client ID',
      });

    new CfnOutput(this, 'CognitoIdentityPoolId', {
      value: identityPool.ref,
      description: 'Cognito Identity Pool ID',
    });

    new CfnOutput(this, 'CognitoUserPoolEndpoint', {
        value: `https://${this.userPoolId}.auth.${this.region}.amazoncognito.com`,
        description: 'Cognito User Pool Endpoint',
    });
   
  }

}

