#!/usr/bin/env python3
"""
TRACE Step Functions Deployment Script

Deploys AWS Step Functions state machines for workflow orchestration.
"""

import boto3
import json
import os
from pathlib import Path

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'dev')
REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize clients
sfn_client = boto3.client('stepfunctions', region_name=REGION)
sns_client = boto3.client('sns', region_name=REGION)
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


def create_sns_topic():
    """Create SNS topic for notifications"""
    
    topic_name = f'TRACE-Notifications-{ENVIRONMENT}'
    
    try:
        response = sns_client.create_topic(
            Name=topic_name,
            Tags=[
                {'Key': 'Project', 'Value': 'TRACE'},
                {'Key': 'Environment', 'Value': ENVIRONMENT}
            ]
        )
        print(f"  Created/found SNS topic: {topic_name}")
        return response['TopicArn']
    except Exception as e:
        print(f"  Error creating SNS topic: {str(e)}")
        return f'arn:aws:sns:{REGION}:{get_account_id()}:{topic_name}'


def deploy_state_machine(name: str, definition_file: str, description: str) -> dict:
    """Deploy a Step Functions state machine"""
    
    print(f"  Deploying: {name}...")
    
    infra = load_infrastructure_outputs()
    account_id = get_account_id()
    
    role_arn = infra.get('iam', {}).get('StepFunctionsRoleArn',
                f'arn:aws:iam::{account_id}:role/TRACE-StepFunctions-Role-{ENVIRONMENT}')
    
    # Read the definition
    definition_path = Path(__file__).parent / definition_file
    with open(definition_path, 'r') as f:
        definition = f.read()
    
    # Replace placeholders
    definition = definition.replace('${Environment}', ENVIRONMENT)
    definition = definition.replace('${Region}', REGION)
    definition = definition.replace('${AccountId}', account_id)
    
    state_machine_name = f'TRACE-{name}-{ENVIRONMENT}'
    
    try:
        # Try to create
        response = sfn_client.create_state_machine(
            name=state_machine_name,
            definition=definition,
            roleArn=role_arn,
            type='STANDARD',
            tags=[
                {'key': 'Project', 'value': 'TRACE'},
                {'key': 'Environment', 'value': ENVIRONMENT}
            ]
        )
        
        print(f"    Created state machine: {state_machine_name}")
        return {
            'name': state_machine_name,
            'arn': response['stateMachineArn'],
            'status': 'created'
        }
        
    except sfn_client.exceptions.StateMachineAlreadyExists:
        # Update existing
        print(f"    State machine exists, updating...")
        
        # Get ARN
        state_machines = sfn_client.list_state_machines()['stateMachines']
        sm_arn = None
        for sm in state_machines:
            if sm['name'] == state_machine_name:
                sm_arn = sm['stateMachineArn']
                break
        
        if sm_arn:
            sfn_client.update_state_machine(
                stateMachineArn=sm_arn,
                definition=definition,
                roleArn=role_arn
            )
            print(f"    Updated state machine: {state_machine_name}")
            return {
                'name': state_machine_name,
                'arn': sm_arn,
                'status': 'updated'
            }
        
    except Exception as e:
        print(f"    Error: {str(e)}")
        return {
            'name': state_machine_name,
            'error': str(e),
            'status': 'failed'
        }


def create_eventbridge_rule(state_machine_arn: str, rule_name: str, schedule: str):
    """Create EventBridge rule to trigger state machine"""
    
    events_client = boto3.client('events', region_name=REGION)
    
    try:
        # Create rule
        events_client.put_rule(
            Name=rule_name,
            ScheduleExpression=schedule,
            State='ENABLED',
            Description=f'TRACE scheduled trigger for {rule_name}'
        )
        
        # Add target
        events_client.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    'Id': 'StepFunctionsTarget',
                    'Arn': state_machine_arn,
                    'RoleArn': f'arn:aws:iam::{get_account_id()}:role/TRACE-StepFunctions-Role-{ENVIRONMENT}',
                    'Input': json.dumps({
                        'triggered_by': 'eventbridge_schedule',
                        'region_id': 'R-E'
                    })
                }
            ]
        )
        
        print(f"    Created EventBridge rule: {rule_name}")
        
    except Exception as e:
        print(f"    Error creating EventBridge rule: {str(e)}")


def main():
    print("=" * 60)
    print("TRACE Step Functions Deployment")
    print("=" * 60)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    print()
    
    # Create SNS topic for notifications
    print("📢 Creating SNS Topic...")
    sns_topic_arn = create_sns_topic()
    
    # Define workflows to deploy
    workflows = [
        {
            'name': 'SelfHealing',
            'file': 'self-healing-workflow.json',
            'description': 'Automated detection and remediation of system issues'
        },
        {
            'name': 'EnergyOptimization',
            'file': 'energy-optimization-workflow.json',
            'description': 'Coordinated TRX shutdown during low traffic periods'
        }
    ]
    
    deployed = []
    
    print("\n🔄 Deploying State Machines...")
    
    for workflow in workflows:
        result = deploy_state_machine(
            workflow['name'],
            workflow['file'],
            workflow['description']
        )
        deployed.append(result)
    
    # Create scheduled triggers
    print("\n⏰ Creating Scheduled Triggers...")
    
    for result in deployed:
        if result.get('arn') and result['name'].endswith('EnergyOptimization' + f'-{ENVIRONMENT}'):
            # Schedule energy optimization to run every 4 hours
            create_eventbridge_rule(
                result['arn'],
                f'TRACE-EnergyOptimization-Schedule-{ENVIRONMENT}',
                'rate(4 hours)'
            )
    
    # Save outputs
    output = {
        'sns_topic_arn': sns_topic_arn,
        'state_machines': deployed
    }
    
    output_file = Path(__file__).parent.parent / 'stepfunctions-outputs.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Step Functions Deployment Complete!")
    print("=" * 60)
    
    print("\nDeployed State Machines:")
    for sm in deployed:
        status_icon = "✅" if sm.get('status') != 'failed' else "❌"
        print(f"  {status_icon} {sm['name']}")
        if sm.get('arn'):
            print(f"      ARN: {sm['arn']}")
    
    print(f"\n📢 SNS Topic: {sns_topic_arn}")
    print(f"\n💾 Outputs saved to: {output_file}")
    print("\nNext step: Run 07-api-gateway/deploy-api.py")
    
    # Print test command
    if deployed and deployed[0].get('arn'):
        print("\n📝 Test your workflow:")
        print(f"""
aws stepfunctions start-execution \\
  --state-machine-arn {deployed[0]['arn']} \\
  --input '{{"issue_type": "agent_unhealthy", "agent_id": "agent-tx005", "severity": "warning", "notification_topic": "{sns_topic_arn}"}}'
        """)


if __name__ == '__main__':
    main()
