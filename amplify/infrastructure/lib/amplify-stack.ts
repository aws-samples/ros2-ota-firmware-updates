import * as cdk from 'aws-cdk-lib';
import * as amplify from '@aws-cdk/aws-amplify-alpha';
import * as codecommit from 'aws-cdk-lib/aws-codecommit';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as path from 'path';
import { Construct } from 'constructs';

export class AmplifyStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create CodeCommit repository
    const repo = new codecommit.Repository(this, 'AmplifyRepo', {
      repositoryName: 'ros2-ota-firmware-updates',
      description: 'Repository for ROS2 OTA Firmware Updates Web Application',
    });

    // Create Lambda function to populate repository
    const populateRepoLambda = new lambda.Function(this, 'PopulateRepoLambda', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'populate_repo.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, 'lambda')),
      timeout: cdk.Duration.minutes(5),
      memorySize: 1024,
      architecture: lambda.Architecture.X86_64,
    });

    // Grant permissions to Lambda
    populateRepoLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'codecommit:CreateRepository',
          'codecommit:GetRepository',
          'codecommit:CreateCommit',
          'codecommit:GetBranch',
          'codecommit:CreateBranch',
          'codecommit:PutFile'
        ],
        resources: [`arn:aws:codecommit:${this.region}:${this.account}:${repo.repositoryName}`],
      })
    );

    // Add CloudWatch Logs permissions
    populateRepoLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:PutLogEvents'
      ],
      resources: ['*']
    }));

    // Create Custom Resource Provider
    const provider = new cr.Provider(this, 'PopulateRepoProvider', {
      onEventHandler: populateRepoLambda,
    });

    // Create Custom Resource
    new cdk.CustomResource(this, 'PopulateRepo', {
      serviceToken: provider.serviceToken,
      properties: {
        RepositoryName: repo.repositoryName,
      },
    });

    // Create Amplify app
    const amplifyApp = new amplify.App(this, 'AmplifyApp', {
      appName: 'ros2-ota-firmware-updates',
      sourceCodeProvider: new amplify.CodeCommitSourceCodeProvider({
        repository: repo,
      }),
      buildSpec: cdk.aws_codebuild.BuildSpec.fromObjectToYaml({
        version: 1,
        backend: {
          phases: {
            build: {
              commands: [
                'yarn add @aws-amplify/backend-cli@^1.4.2 @aws-amplify/backend@^1.7.0 aws-cdk-lib@^2.167.1 constructs@^10.4.2',
                'yarn install --frozen-lockfile',
                'yarn ampx pipeline-deploy --branch $AWS_BRANCH --app-id $AWS_APP_ID'
              ]
            },
        }},
        frontend: {
          phases: {
            build: {
              commands: [
                'yarn run build'
              ]
            }
          },
          artifacts: {
            baseDirectory: 'build',
            files: [
              '**/*'
            ]
          },
          cache: {
            paths: [
              'node_modules/**/*'
            ]
          }
        }
      }),
      environmentVariables: {
        NODE_ENV: 'production',
        AMPLIFY_MONOREPO_APP_ROOT: '/',
        AMPLIFY_DIFF_DEPLOY: 'false',
        _LIVE_UPDATES: JSON.stringify([
          {
            name: 'Amplify CLI',
            pkg: '@aws-amplify/cli',
            type: 'npm',
            version: 'latest'
          },
          {
            name: 'Node.js version',
            pkg: 'node',
            type: 'nvm',
            version: '20.18.1'
          }
        ])
      }
    });

    // Add branch with auto build and environment variables
    const main = amplifyApp.addBranch('main', {
      autoBuild: true,
      stage: 'PRODUCTION',
      environmentVariables: {
        NODE_ENV: 'production'
      }
    });

    // Build specification
    amplifyApp.addCustomRule(amplify.CustomRule.SINGLE_PAGE_APPLICATION_REDIRECT);

    // Add managed policy to Amplify app role
    const amplifyRole = amplifyApp.node.findChild('Role') as iam.Role;
    amplifyRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmplifyBackendDeployFullAccess')
    );

    // Output the repository clone URL and other useful information
    new cdk.CfnOutput(this, 'RepositoryCloneUrlHttp', {
      value: repo.repositoryCloneUrlHttp,
      description: 'CodeCommit Repository Clone URL (HTTPS)',
    });

    new cdk.CfnOutput(this, 'AmplifyAppId', {
      value: amplifyApp.appId,
      description: 'Amplify App ID',
    });

    new cdk.CfnOutput(this, 'AmplifyAppDefaultDomain', {
      value: `https://${main.branchName}.${amplifyApp.defaultDomain}`,
      description: 'Amplify App Default Domain URL',
    });
  }
}