#!/usr/bin/env python3
"""
TRACE Agent Testing Script

Tests the deployed Bedrock agents and Lambda tools.
"""

import boto3
import json
import os
import sys
from pathlib import Path

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'dev')
REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize clients
lambda_client = boto3.client('lambda', region_name=REGION)
bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)


def load_agent_info():
    """Load agent information from deployment"""
    output_file = Path(__file__).parent.parent / 'agent-info.json'
    if output_file.exists():
        with open(output_file, 'r') as f:
            return json.load(f)
    return {}


def test_health_monitor():
    """Test the Health Monitor Lambda tool"""
    
    print("\n🔍 Testing Health Monitor Tool...")
    
    function_name = f'TRACE-HealthMonitor-{ENVIRONMENT}'
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'check_system_health',
                'parameters': {}
            })
        )
        
        result = json.loads(response['Payload'].read())
        body = json.loads(result.get('body', '{}'))
        
        print(f"  ✅ Status: {body.get('overall_status', 'unknown')}")
        print(f"  ✅ Health Score: {body.get('health_score', 'N/A')}")
        
        if body.get('issues'):
            print(f"  ⚠️ Issues detected: {len(body['issues'])}")
        
        return True
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"  ❌ Function not found: {function_name}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def test_remediation():
    """Test the Remediation Lambda tool"""
    
    print("\n🔧 Testing Remediation Tool...")
    
    function_name = f'TRACE-Remediation-{ENVIRONMENT}'
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'restart_agent',
                'parameters': {
                    'agent_id': 'test-agent-001',
                    'reason': 'test_run'
                }
            })
        )
        
        result = json.loads(response['Payload'].read())
        body = json.loads(result.get('body', '{}'))
        
        print(f"  ✅ Operation: {body.get('operation', 'unknown')}")
        print(f"  ✅ Success: {body.get('success', False)}")
        print(f"  ✅ Message: {body.get('message', 'N/A')}")
        
        return True
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"  ❌ Function not found: {function_name}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def test_telemetry_query():
    """Test the Telemetry Query Lambda tool"""
    
    print("\n📊 Testing Telemetry Query Tool...")
    
    function_name = f'TRACE-TelemetryQuery-{ENVIRONMENT}'
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_tower_metrics',
                'parameters': {
                    'tower_id': 'TX001'
                }
            })
        )
        
        result = json.loads(response['Payload'].read())
        body = json.loads(result.get('body', '{}'))
        
        print(f"  ✅ Tower: {body.get('tower_id', 'unknown')}")
        print(f"  ✅ Source: {body.get('source', 'unknown')}")
        
        metrics = body.get('metrics', {})
        print(f"  ✅ Connected Users: {metrics.get('connected_users', 'N/A')}")
        print(f"  ✅ CPU Utilization: {metrics.get('cpu_util_pct', 'N/A')}%")
        
        return True
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"  ❌ Function not found: {function_name}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def test_bedrock_agent():
    """Test the Bedrock Principal Agent"""
    
    print("\n🤖 Testing Bedrock Principal Agent...")
    
    agent_info = load_agent_info()
    principal = agent_info.get('principal_agent', {})
    
    agent_id = principal.get('agent_id')
    alias_id = principal.get('alias_id')
    
    if not agent_id or not alias_id:
        print("  ⚠️ Agent not configured. Skipping Bedrock test.")
        print("  Run 05-bedrock-agents/deploy-agents.py first.")
        return False
    
    try:
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId='test-session-001',
            inputText='Check the overall system health and provide a brief summary.'
        )
        
        # Collect response
        result_text = ""
        for event in response['completion']:
            if 'chunk' in event:
                result_text += event['chunk']['bytes'].decode('utf-8')
        
        print(f"  ✅ Agent responded successfully")
        print(f"  Response preview: {result_text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        print("  Make sure you have access to Claude models in Bedrock.")
        return False


def test_api():
    """Test the API Gateway endpoint"""
    
    print("\n🌐 Testing API Gateway...")
    
    api_file = Path(__file__).parent.parent / 'api-outputs.json'
    
    if not api_file.exists():
        print("  ⚠️ API not deployed. Skipping API test.")
        return False
    
    with open(api_file, 'r') as f:
        api_info = json.load(f)
    
    api_url = api_info.get('rest_api', {}).get('api_url')
    
    if not api_url:
        print("  ⚠️ API URL not found.")
        return False
    
    import urllib.request
    
    try:
        health_url = f"{api_url}/health"
        print(f"  Testing: {health_url}")
        
        req = urllib.request.Request(health_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"  ✅ API responded: {data.get('overall_status', 'unknown')}")
            return True
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("TRACE Agent Testing")
    print("=" * 60)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    
    results = {}
    
    # Test Lambda tools
    results['health_monitor'] = test_health_monitor()
    results['remediation'] = test_remediation()
    results['telemetry_query'] = test_telemetry_query()
    
    # Test Bedrock agent
    results['bedrock_agent'] = test_bedrock_agent()
    
    # Test API
    results['api'] = test_api()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
