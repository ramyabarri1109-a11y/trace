#!/usr/bin/env python3
"""
TRACE API Gateway Deployment Script

Deploys REST and WebSocket APIs for the TRACE dashboard.
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
apigateway = boto3.client('apigateway', region_name=REGION)
apigatewayv2 = boto3.client('apigatewayv2', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
sts_client = boto3.client('sts', region_name=REGION)

def get_account_id():
    return sts_client.get_caller_identity()['Account']

def load_infrastructure_outputs():
    output_file = Path(__file__).parent.parent / 'infrastructure-outputs.json'
    if output_file.exists():
        with open(output_file, 'r') as f:
            return json.load(f)
    return {}


def deploy_api_lambda():
    """Deploy the API handler Lambda function"""
    
    print("  Deploying API handler Lambda...")
    
    infra = load_infrastructure_outputs()
    account_id = get_account_id()
    role_arn = infra.get('iam', {}).get('LambdaRoleArn',
                f'arn:aws:iam::{account_id}:role/TRACE-Lambda-Role-{ENVIRONMENT}')
    
    function_name = f'TRACE-APIHandler-{ENVIRONMENT}'
    
    # Package the function
    lambda_dir = Path(__file__).parent / 'lambda-handler'
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        zip_path = tmp.name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        handler_file = lambda_dir / 'handler.py'
        if handler_file.exists():
            zf.write(handler_file, 'handler.py')
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"    Updated: {function_name}")
    except lambda_client.exceptions.ResourceNotFoundException:
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='TRACE API Handler',
            Timeout=30,
            MemorySize=256,
            Environment={
                'Variables': {'ENVIRONMENT': ENVIRONMENT}
            }
        )
        print(f"    Created: {function_name}")
    
    os.unlink(zip_path)
    
    return f'arn:aws:lambda:{REGION}:{account_id}:function:{function_name}'


def create_rest_api(lambda_arn: str):
    """Create REST API"""
    
    print("\n  Creating REST API...")
    
    api_name = f'TRACE-API-{ENVIRONMENT}'
    
    # Check if API exists
    apis = apigateway.get_rest_apis()['items']
    api_id = None
    for api in apis:
        if api['name'] == api_name:
            api_id = api['id']
            print(f"    Found existing API: {api_id}")
            break
    
    if not api_id:
        # Create new API
        response = apigateway.create_rest_api(
            name=api_name,
            description='TRACE Dashboard API',
            endpointConfiguration={'types': ['REGIONAL']}
        )
        api_id = response['id']
        print(f"    Created API: {api_id}")
    
    # Get root resource
    resources = apigateway.get_resources(restApiId=api_id)['items']
    root_id = None
    for resource in resources:
        if resource['path'] == '/':
            root_id = resource['id']
            break
    
    # Create resources and methods
    endpoints = [
        {'path': 'health', 'methods': ['GET']},
        {'path': 'agent', 'methods': ['POST']},
        {'path': 'telemetry', 'methods': ['GET']},
        {'path': 'remediate', 'methods': ['POST']}
    ]
    
    for endpoint in endpoints:
        try:
            # Create resource
            resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=root_id,
                pathPart=endpoint['path']
            )
            resource_id = resource['id']
        except apigateway.exceptions.ConflictException:
            # Resource exists
            for r in resources:
                if r['path'] == f"/{endpoint['path']}":
                    resource_id = r['id']
                    break
        
        # Create methods
        for method in endpoint['methods']:
            try:
                apigateway.put_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method,
                    authorizationType='NONE'
                )
                
                # Add Lambda integration
                apigateway.put_integration(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method,
                    type='AWS_PROXY',
                    integrationHttpMethod='POST',
                    uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
                )
            except:
                pass
        
        # Add CORS (OPTIONS)
        try:
            apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            apigateway.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            )
            apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
        except:
            pass
    
    # Deploy API
    try:
        apigateway.create_deployment(
            restApiId=api_id,
            stageName=ENVIRONMENT,
            description=f'TRACE API deployment - {ENVIRONMENT}'
        )
        print(f"    Deployed to stage: {ENVIRONMENT}")
    except Exception as e:
        print(f"    Deployment note: {str(e)}")
    
    # Add Lambda permission
    try:
        lambda_client.add_permission(
            FunctionName=lambda_arn.split(':')[-1],
            StatementId=f'APIGateway-{api_id}',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f'arn:aws:execute-api:{REGION}:{get_account_id()}:{api_id}/*'
        )
    except:
        pass
    
    api_url = f'https://{api_id}.execute-api.{REGION}.amazonaws.com/{ENVIRONMENT}'
    print(f"    API URL: {api_url}")
    
    return {
        'api_id': api_id,
        'api_url': api_url
    }


def main():
    print("=" * 60)
    print("TRACE API Gateway Deployment")
    print("=" * 60)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    print()
    
    # Deploy API Lambda
    print("🔧 Deploying API Lambda...")
    lambda_arn = deploy_api_lambda()
    
    # Create REST API
    print("\n🌐 Creating REST API...")
    rest_api = create_rest_api(lambda_arn)
    
    # Save outputs
    output = {
        'lambda_arn': lambda_arn,
        'rest_api': rest_api
    }
    
    output_file = Path(__file__).parent.parent / 'api-outputs.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ API Gateway Deployment Complete!")
    print("=" * 60)
    
    print(f"\n🌐 REST API URL: {rest_api['api_url']}")
    print(f"\n💾 Outputs saved to: {output_file}")
    
    print("\n📝 Test your API:")
    print(f"  curl {rest_api['api_url']}/health")
    
    print("\nNext step: Run 08-frontend/deploy-frontend.py")


if __name__ == '__main__':
    main()
