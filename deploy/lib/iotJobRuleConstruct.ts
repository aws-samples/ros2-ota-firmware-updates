// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as pythonlambda from '@aws-cdk/aws-lambda-python-alpha';

interface IotJobRuleConstructProps extends cdk.StackProps {

}

// Create a cdk construct named IotJobRuleConstruct
export class IotJobRuleConstruct extends Construct {
    constructor(scope: Construct, id: string, props: IotJobRuleConstructProps) {
        super(scope, id);
        // Create a python lambda function
        const iotJobUpdateFunction = new pythonlambda.PythonFunction(this, 'iotJobUpdateFunction', {
        entry: 'lambda/iotJobUpdateFunction',
        runtime: cdk.aws_lambda.Runtime.PYTHON_3_12,
        });

        // Create an IoT rule that acccepts messages from '$aws/events/jobExecution/#' and triggers a python lambda function
        const iotRule = new cdk.aws_iot.CfnTopicRule(this, 'iotRule', {
        ruleName: 'RosJobExecutionRule',
        topicRulePayload: {
            actions: [{ lambda: { functionArn: iotJobUpdateFunction.functionArn } }],
            sql: "SELECT * FROM '$aws/events/jobExecution/#'",
            awsIotSqlVersion: '2015-10-08',
        }
        });
        // Grant permissions for IoT rule to invoke the python lambda function
        iotJobUpdateFunction.grantInvoke(new cdk.aws_iam.ServicePrincipal('iot.amazonaws.com'));

        iotJobUpdateFunction.addToRolePolicy(new cdk.aws_iam.PolicyStatement({
            actions: ['iot:GetJobDocument'],
            resources: ['*'], 
        }));
        iotJobUpdateFunction.addToRolePolicy(new cdk.aws_iam.PolicyStatement({
            actions: ['iot:UpdateThingShadow', 'iot:UpdateThing'],
            resources: [cdk.Arn.format({
                service: 'iot',
                resource: 'thing',
                resourceName: 'device-thing-*',
            }, cdk.Stack.of(this))], 
        }));

    }
}