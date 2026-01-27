#!/usr/bin/env python3
"""
TRACE Agent Tools Deployment Script

Deploys Lambda functions that serve as tools for Bedrock Agents.
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
lambda_client = boto3.client('lambda', region_name=REGION)
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


def package_lambda(tool_dir: Path) -> str:
    """Package Lambda function code"""
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        zip_path = tmp.name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        handler_file = tool_dir / 'handler.py'
        if handler_file.exists():
            zf.write(handler_file, 'handler.py')
        
        # Include any additional Python files
        for py_file in tool_dir.glob('*.py'):
            if py_file.name != 'handler.py':
                zf.write(py_file, py_file.name)
    
    return zip_path


def deploy_tool(tool_name: str, tool_dir: Path, description: str):
    """Deploy a Lambda function as an agent tool"""
    
    infra = load_infrastructure_outputs()
    account_id = get_account_id()
    role_arn = infra.get('iam', {}).get('LambdaRoleArn',
                f'arn:aws:iam::{account_id}:role/TRACE-Lambda-Role-{ENVIRONMENT}')
    
    function_name = f'TRACE-{tool_name}-{ENVIRONMENT}'
    
    # Package the function
    zip_path = package_lambda(tool_dir)
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        # Try to update existing function
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"  Updated: {function_name}")
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Description=description,
            Timeout=60,
            MemorySize=256,
            Environment={
                'Variables': {
                    'ENVIRONMENT': ENVIRONMENT
                }
            }
        )
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': zip_content},
            Description=description,
            Timeout=60,
            MemorySize=256,
            Environment={
                'Variables': {
                    'ENVIRONMENT': ENVIRONMENT
                }
            },
            Tags={
                'Project': 'TRACE',
                'Environment': ENVIRONMENT,
                'Type': 'AgentTool'
            }
        )
        print(f"  Created: {function_name}")
    
    # Clean up
    os.unlink(zip_path)
    
    # Add resource-based policy for Bedrock
    add_bedrock_permission(function_name)
    
    return function_name


def add_bedrock_permission(function_name: str):
    """Add permission for Bedrock to invoke the Lambda function"""
    
    try:
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId='AllowBedrockInvoke',
            Action='lambda:InvokeFunction',
            Principal='bedrock.amazonaws.com',
            SourceAccount=get_account_id()
        )
        print(f"    Added Bedrock invoke permission")
    except lambda_client.exceptions.ResourceConflictException:
        # Permission already exists
        pass
    except Exception as e:
        print(f"    Note: {str(e)}")


def main():
    print("=" * 60)
    print("TRACE Agent Tools Deployment")
    print("=" * 60)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    print()
    
    base_dir = Path(__file__).parent
    
    # Define tools to deploy
    tools = [
        {
            'name': 'HealthMonitor',
            'dir': 'health-monitor',
            'description': 'TRACE Health Monitor - Checks system and agent health status'
        },
        {
            'name': 'Remediation',
            'dir': 'remediation',
            'description': 'TRACE Remediation - Executes restart, redeploy, reroute actions'
        },
        {
            'name': 'TelemetryQuery',
            'dir': 'telemetry-query',
            'description': 'TRACE Telemetry Query - Queries telemetry data from storage'
        }
    ]
    
    deployed_functions = []
    
    for tool in tools:
        print(f"\n🔧 Deploying {tool['name']}...")
        tool_dir = base_dir / tool['dir']
        
        if not tool_dir.exists():
            print(f"  ⚠️ Directory not found: {tool_dir}")
            continue
        
        function_name = deploy_tool(tool['name'], tool_dir, tool['description'])
        deployed_functions.append(function_name)
    
    print("\n" + "=" * 60)
    print("✅ Agent Tools Deployment Complete!")
    print("=" * 60)
    print("\nDeployed tools:")
    for fn in deployed_functions:
        print(f"  • {fn}")
    
    # Save tool ARNs for Bedrock agent setup
    tool_arns = {
        'tools': [
            {
                'name': fn.replace(f'-{ENVIRONMENT}', '').replace('TRACE-', ''),
                'function_name': fn,
                'arn': f'arn:aws:lambda:{REGION}:{get_account_id()}:function:{fn}'
            }
            for fn in deployed_functions
        ]
    }
    
    output_file = Path(__file__).parent.parent / 'tool-arns.json'
    with open(output_file, 'w') as f:
        json.dump(tool_arns, f, indent=2)
    
    print(f"\n💾 Tool ARNs saved to: {output_file}")
    print("\nNext step: Run 05-bedrock-agents/deploy-agents.py")


if __name__ == '__main__':
    main()
