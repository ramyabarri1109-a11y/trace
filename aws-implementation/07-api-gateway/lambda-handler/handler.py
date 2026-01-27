"""
TRACE API Handler Lambda

Handles REST API requests for the TRACE dashboard.
"""

import json
import boto3
import os
from datetime import datetime

# Initialize clients
lambda_client = boto3.client('lambda')
bedrock_runtime = boto3.client('bedrock-agent-runtime')

ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')


def lambda_handler(event, context):
    """
    Main handler for API Gateway requests.
    """
    
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    body = event.get('body')
    
    if body and isinstance(body, str):
        try:
            body = json.loads(body)
        except:
            body = {}
    
    # Route requests
    routes = {
        ('GET', '/health'): handle_health,
        ('GET', '/health/'): handle_health,
        ('POST', '/agent/invoke'): handle_agent_invoke,
        ('POST', '/agent'): handle_agent,
        ('GET', '/telemetry'): handle_get_telemetry,
        ('POST', '/remediate'): handle_remediate,
    }
    
    # Find matching route
    handler = routes.get((http_method, path))
    
    # Try path prefix matching
    if not handler:
        for (method, route_path), route_handler in routes.items():
            if method == http_method and path.startswith(route_path.rstrip('/')):
                handler = route_handler
                break
    
    if handler:
        try:
            result = handler(event, body)
            return create_response(200, result)
        except Exception as e:
            return create_response(500, {'error': str(e)})
    else:
        return create_response(404, {'error': 'Not found'})


def handle_health(event, body):
    """Get system health status"""
    
    try:
        # Invoke health monitor Lambda
        response = lambda_client.invoke(
            FunctionName=f'TRACE-HealthMonitor-{ENVIRONMENT}',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'check_system_health',
                'parameters': {}
            })
        )
        
        result = json.loads(response['Payload'].read())
        return json.loads(result.get('body', '{}'))
        
    except Exception as e:
        # Return demo data on error
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'health_score': 94.5,
            'components': {
                'agents': {'total': 15, 'healthy': 14, 'unhealthy': 1},
                'infrastructure': {'status': 'healthy', 'active_towers': 47}
            },
            'source': 'demo'
        }


def handle_agent(event, body):
    """Handle agent requests - chat and analysis"""
    
    prompt = body.get('prompt', body.get('message', 'Check system health'))
    session_id = body.get('session_id', f"session-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    
    # Use hardcoded agent IDs
    agent_id = 'N3LVTOXSFA'
    alias_id = 'TSTALIASID'
    
    try:
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText=prompt
        )
        
        # Collect response
        result_text = ""
        for event_item in response['completion']:
            if 'chunk' in event_item:
                result_text += event_item['chunk']['bytes'].decode('utf-8')
        
        return {
            'response': result_text,
            'session_id': session_id,
            'source': 'principal_agent',
            'success': True
        }
        
    except Exception as e:
        # Fallback response
        return {
            'response': f'I apologize, but I encountered an issue processing your request. Error: {str(e)[:100]}',
            'prompt': prompt,
            'source': 'fallback',
            'success': False
        }


def handle_agent_invoke(event, body):
    """Invoke Bedrock agent with a prompt"""
    
    prompt = body.get('prompt', 'Check system health')
    session_id = body.get('session_id', 'api-session-001')
    
    # Load agent info
    try:
        with open('/tmp/agent-info.json', 'r') as f:
            agent_info = json.load(f)
    except:
        agent_info = {}
    
    agent_id = agent_info.get('principal_agent', {}).get('agent_id')
    alias_id = agent_info.get('principal_agent', {}).get('alias_id')
    
    if not agent_id or not alias_id:
        return {
            'response': f'Agent not configured. Your prompt: "{prompt}"',
            'source': 'fallback'
        }
    
    try:
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText=prompt
        )
        
        # Collect response
        result_text = ""
        for event in response['completion']:
            if 'chunk' in event:
                result_text += event['chunk']['bytes'].decode('utf-8')
        
        return {
            'response': result_text,
            'session_id': session_id,
            'source': 'bedrock_agent'
        }
        
    except Exception as e:
        return {
            'response': f'Error invoking agent: {str(e)}',
            'prompt': prompt,
            'source': 'error'
        }


def handle_get_telemetry(event, body):
    """Get telemetry data"""
    
    # Get region from path or query
    path_params = event.get('pathParameters', {}) or {}
    query_params = event.get('queryStringParameters', {}) or {}
    
    region_id = path_params.get('region') or query_params.get('region', 'R-E')
    
    try:
        response = lambda_client.invoke(
            FunctionName=f'TRACE-TelemetryQuery-{ENVIRONMENT}',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_regional_metrics',
                'parameters': {'region_id': region_id}
            })
        )
        
        result = json.loads(response['Payload'].read())
        return json.loads(result.get('body', '{}'))
        
    except Exception as e:
        return {
            'region_id': region_id,
            'error': str(e),
            'source': 'error'
        }


def handle_remediate(event, body):
    """Execute remediation action"""
    
    # Pass the entire body to the remediation Lambda
    # Body includes: issueId, action, region
    issue_id = body.get('issueId', 'unknown')
    action = body.get('action', 'auto_remediate')
    region = body.get('region', 'us-east-1')
    
    try:
        response = lambda_client.invoke(
            FunctionName=f'TRACE-Remediation-{ENVIRONMENT}',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'body': json.dumps({
                    'issueId': issue_id,
                    'action': action,
                    'region': region
                })
            })
        )
        
        result = json.loads(response['Payload'].read())
        return json.loads(result.get('body', '{}'))
        
    except Exception as e:
        return {
            'issueId': issue_id,
            'action': action,
            'error': str(e),
            'source': 'error'
        }


def create_response(status_code, body):
    """Create API Gateway response"""
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body)
    }
