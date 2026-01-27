#!/usr/bin/env python3
"""
TRACE Data Pipeline Setup Script

Deploys Kinesis streams, Lambda processor, and Timestream database.
"""

import boto3
import json
import os
import zipfile
import tempfile
from pathlib import Path

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'dev')
REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize clients
cf_client = boto3.client('cloudformation', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
timestream_client = boto3.client('timestream-write', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)
sts_client = boto3.client('sts', region_name=REGION)

def get_account_id():
    return sts_client.get_caller_identity()['Account']

def load_infrastructure_outputs():
    """Load outputs from infrastructure setup"""
    output_file = Path(__file__).parent.parent / 'infrastructure-outputs.json'
    if output_file.exists():
        with open(output_file, 'r') as f:
            return json.load(f)
    return {}

def deploy_kinesis_streams():
    """Deploy Kinesis streams using CloudFormation"""
    print("\n📊 Deploying Kinesis Streams...")
    
    template_path = Path(__file__).parent / 'kinesis-streams.yaml'
    with open(template_path, 'r') as f:
        template_body = f.read()
    
    stack_name = f'trace-kinesis-{ENVIRONMENT}'
    
    try:
        try:
            cf_client.describe_stacks(StackName=stack_name)
            print(f"  Updating stack: {stack_name}")
            cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=[
                    {'ParameterKey': 'Environment', 'ParameterValue': ENVIRONMENT}
                ]
            )
        except cf_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                print(f"  Creating stack: {stack_name}")
                cf_client.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=[
                        {'ParameterKey': 'Environment', 'ParameterValue': ENVIRONMENT}
                    ]
                )
            elif 'No updates' in str(e):
                print(f"  Stack {stack_name} is up to date")
                return
            else:
                raise
        
        # Wait for completion
        waiter = cf_client.get_waiter('stack_create_complete')
        try:
            waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 30})
        except:
            waiter = cf_client.get_waiter('stack_update_complete')
            waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 30})
        
        print("  ✅ Kinesis streams deployed")
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

def create_timestream_database():
    """Create Timestream database and table"""
    print("\n⏱️ Creating Timestream Database...")
    
    database_name = f'TRACE-Telemetry-{ENVIRONMENT}'
    table_name = 'TowerMetrics'
    
    # Create database
    try:
        timestream_client.create_database(DatabaseName=database_name)
        print(f"  Created database: {database_name}")
    except timestream_client.exceptions.ConflictException:
        print(f"  Database {database_name} already exists")
    except Exception as e:
        print(f"  Error creating database: {str(e)}")
        return
    
    # Create table
    try:
        timestream_client.create_table(
            DatabaseName=database_name,
            TableName=table_name,
            RetentionProperties={
                'MemoryStoreRetentionPeriodInHours': 24,  # Hot storage: 24 hours
                'MagneticStoreRetentionPeriodInDays': 365  # Cold storage: 1 year
            },
            MagneticStoreWriteProperties={
                'EnableMagneticStoreWrites': True
            }
        )
        print(f"  Created table: {table_name}")
    except timestream_client.exceptions.ConflictException:
        print(f"  Table {table_name} already exists")
    except Exception as e:
        print(f"  Error creating table: {str(e)}")
    
    print("  ✅ Timestream setup complete")

def package_lambda():
    """Package Lambda function code"""
    print("\n📦 Packaging Lambda function...")
    
    lambda_dir = Path(__file__).parent / 'lambda-processor'
    
    # Create zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        zip_path = tmp.name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        handler_file = lambda_dir / 'handler.py'
        if handler_file.exists():
            zf.write(handler_file, 'handler.py')
    
    print(f"  Created package: {zip_path}")
    return zip_path

def deploy_lambda_processor():
    """Deploy Lambda function for telemetry processing"""
    print("\n🔧 Deploying Lambda Processor...")
    
    infra = load_infrastructure_outputs()
    account_id = get_account_id()
    
    function_name = f'TRACE-TelemetryProcessor-{ENVIRONMENT}'
    role_arn = infra.get('iam', {}).get('LambdaRoleArn', 
                f'arn:aws:iam::{account_id}:role/TRACE-Lambda-Role-{ENVIRONMENT}')
    
    # Package the function
    zip_path = package_lambda()
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    # Create or update function
    try:
        # Try to update existing function
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"  Updated function: {function_name}")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='TRACE Telemetry Processor - processes Kinesis telemetry data',
            Timeout=60,
            MemorySize=256,
            Environment={
                'Variables': {
                    'ENVIRONMENT': ENVIRONMENT,
                    'TIMESTREAM_DATABASE': f'TRACE-Telemetry-{ENVIRONMENT}',
                    'TIMESTREAM_TABLE': 'TowerMetrics',
                    'DYNAMODB_TABLE': f'TRACE-TelemetryAggregates-{ENVIRONMENT}'
                }
            },
            Tags={
                'Project': 'TRACE',
                'Environment': ENVIRONMENT
            }
        )
        print(f"  Created function: {function_name}")
    
    # Clean up temp file
    os.unlink(zip_path)
    
    # Add Kinesis trigger
    add_kinesis_trigger(function_name)
    
    print("  ✅ Lambda processor deployed")

def add_kinesis_trigger(function_name: str):
    """Add Kinesis stream as event source for Lambda"""
    print("  Adding Kinesis trigger...")
    
    account_id = get_account_id()
    stream_arn = f'arn:aws:kinesis:{REGION}:{account_id}:stream/TRACE-TowerTelemetry-{ENVIRONMENT}'
    
    # Check if event source mapping exists
    try:
        mappings = lambda_client.list_event_source_mappings(
            FunctionName=function_name,
            EventSourceArn=stream_arn
        )
        
        if mappings['EventSourceMappings']:
            print("    Kinesis trigger already exists")
            return
    except Exception as e:
        print(f"    Note: {str(e)}")
    
    # Create event source mapping
    try:
        lambda_client.create_event_source_mapping(
            FunctionName=function_name,
            EventSourceArn=stream_arn,
            BatchSize=100,
            StartingPosition='LATEST',
            MaximumBatchingWindowInSeconds=5
        )
        print("    Kinesis trigger added")
    except Exception as e:
        print(f"    Error adding trigger: {str(e)}")

def main():
    print("=" * 60)
    print("TRACE Data Pipeline Setup")
    print("=" * 60)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    
    # Step 1: Deploy Kinesis Streams
    deploy_kinesis_streams()
    
    # Step 2: Create Timestream Database
    create_timestream_database()
    
    # Step 3: Deploy Lambda Processor
    deploy_lambda_processor()
    
    print("\n" + "=" * 60)
    print("✅ Data Pipeline Setup Complete!")
    print("=" * 60)
    print("\nNext step: Run 03-ml-models/deploy-models.py")

if __name__ == '__main__':
    main()
