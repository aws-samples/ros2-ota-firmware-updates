import { defineBackend } from '@aws-amplify/backend';
import { auth } from './auth/resource';
import { data } from './data/resource';
import { LambdaStack } from './custom-functions/resources';
import { UserPool } from 'aws-cdk-lib/aws-cognito';

/**
 * @see https://docs.amplify.aws/react/build-a-backend/ to add storage, functions, and more
 */
const backend = defineBackend({});

const lambdaStack = new LambdaStack(
  backend.createStack('LambdaStack'),
  'lambdaResources',
  {}
);

backend.addOutput({
  custom: {
    api_id: lambdaStack.apiId,
    api_endpoint: lambdaStack.apiEndpoint,
  },
  auth: {
    identity_pool_id: lambdaStack.identityPoolId,
    aws_region: "us-east-1",
    unauthenticated_identities_enabled: false,
    user_pool_id: lambdaStack.userPoolId,
    user_pool_client_id: lambdaStack.userPoolClientId
  }
});
