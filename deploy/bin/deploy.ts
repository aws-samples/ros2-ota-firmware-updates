#!/usr/bin/env node
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0


import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { DeployStack } from '../lib/deploy-stack';

const app = new cdk.App();
new DeployStack(app, 'DeployStack', {

  /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
});