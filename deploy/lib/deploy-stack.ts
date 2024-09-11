// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { IotJobRuleConstruct } from './iotJobRuleConstruct';

export class DeployStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create an ECR repository
    const ecrRepository = new cdk.aws_ecr.Repository(this, 'ecrRepository', {
      repositoryName: 'firmware-image-repository',
    });

    const iotJobRuleConstruct = new IotJobRuleConstruct(this, 'IotJobRuleConstruct', {});
  }
}
