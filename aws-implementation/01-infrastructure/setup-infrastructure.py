#!/usr/bin/env python3
"""
TRACE Infrastructure Setup Script

This script deploys all foundational AWS infrastructure for TRACE.
"""

import boto3
import json
import time
import os
from pathlib import Path

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'dev')
REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize clients
cf_client = boto3.client('cloudformation', region_name=REGION)
sts_client = boto3.client('sts', region_name=REGION)

def get_account_id():
    """Get AWS account ID"""
    return sts_client.get_caller_identity()['Account']

def deploy_stack(stack_name: str, template_file: str, capabilities: list = None):
    """Deploy a CloudFormation stack"""
    
    template_path = Path(__file__).parent / template_file
    with open(template_path, 'r') as f:
        template_body = f.read()
    
    params = {
        'StackName': stack_name,
        'TemplateBody': template_body,
        'Parameters': [
            {'ParameterKey': 'Environment', 'ParameterValue': ENVIRONMENT}
        ],
        'Tags': [
            {'Key': 'Project', 'Value': 'TRACE'},
            {'Key': 'Environment', 'Value': ENVIRONMENT},
            {'Key': 'ManagedBy', 'Value': 'CloudFormation'}
        ]
    }
    
    if capabilities:
        params['Capabilities'] = capabilities
    
    try:
        # Check if stack exists
        try:
            cf_client.describe_stacks(StackName=stack_name)
            # Stack exists, update it
            print(f"  Updating existing stack: {stack_name}")
            cf_client.update_stack(**params)
        except cf_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                # Stack doesn't exist, create it
                print(f"  Creating new stack: {stack_name}")
                cf_client.create_stack(**params)
            elif 'No updates are to be performed' in str(e):
                print(f"  Stack {stack_name} is already up to date")
                return True
            else:
                raise
        
        # Wait for stack operation to complete
        print(f"  Waiting for stack {stack_name} to complete...")
        waiter = cf_client.get_waiter('stack_create_complete')
        try:
            waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 60})
        except:
            waiter = cf_client.get_waiter('stack_update_complete')
            waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 60})
        
        print(f"  ✅ Stack {stack_name} deployed successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Error deploying {stack_name}: {str(e)}")
        return False

def get_stack_outputs(stack_name: str) -> dict:
    """Get outputs from a CloudFormation stack"""
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        outputs = response['Stacks'][0].get('Outputs', [])
        return {o['OutputKey']: o['OutputValue'] for o in outputs}
    except:
        return {}

def main():
    print("=" * 60)
    print("TRACE Infrastructure Setup")
    print("=" * 60)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    print(f"Account ID: {get_account_id()}")
    print("=" * 60)
    
    # Step 1: Deploy IAM Roles
    print("\n📋 Step 1: Deploying IAM Roles...")
    iam_success = deploy_stack(
        f'trace-iam-roles-{ENVIRONMENT}',
        'iam-roles.yaml',
        capabilities=['CAPABILITY_NAMED_IAM']
    )
    
    if not iam_success:
        print("❌ IAM deployment failed. Exiting.")
        return
    
    # Step 2: Deploy DynamoDB Tables
    print("\n📊 Step 2: Deploying DynamoDB Tables...")
    dynamodb_success = deploy_stack(
        f'trace-dynamodb-{ENVIRONMENT}',
        'dynamodb-tables.yaml'
    )
    
    # Step 3: Deploy S3 Buckets
    print("\n🪣 Step 3: Deploying S3 Buckets...")
    s3_success = deploy_stack(
        f'trace-s3-{ENVIRONMENT}',
        's3-buckets.yaml'
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    # Get outputs
    iam_outputs = get_stack_outputs(f'trace-iam-roles-{ENVIRONMENT}')
    dynamodb_outputs = get_stack_outputs(f'trace-dynamodb-{ENVIRONMENT}')
    s3_outputs = get_stack_outputs(f'trace-s3-{ENVIRONMENT}')
    
    print("\n🔐 IAM Roles Created:")
    for key, value in iam_outputs.items():
        print(f"  • {key}: {value}")
    
    print("\n📊 DynamoDB Tables Created:")
    for key, value in dynamodb_outputs.items():
        print(f"  • {key}: {value}")
    
    print("\n🪣 S3 Buckets Created:")
    for key, value in s3_outputs.items():
        print(f"  • {key}: {value}")
    
    # Save outputs for other scripts
    all_outputs = {
        'environment': ENVIRONMENT,
        'region': REGION,
        'account_id': get_account_id(),
        'iam': iam_outputs,
        'dynamodb': dynamodb_outputs,
        's3': s3_outputs
    }
    
    output_file = Path(__file__).parent.parent / 'infrastructure-outputs.json'
    with open(output_file, 'w') as f:
        json.dump(all_outputs, f, indent=2)
    
    print(f"\n💾 Outputs saved to: {output_file}")
    print("\n✅ Infrastructure setup complete!")
    print("\nNext step: Run 02-data-pipeline/setup-pipeline.py")

if __name__ == '__main__':
    main()
