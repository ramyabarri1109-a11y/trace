"""
TRACE Health Monitor Tool

This Lambda function provides health monitoring capabilities for Bedrock Agents.
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize clients
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event, context):
    """
    Health Monitor Tool for Bedrock Agent
    
    Supported actions:
    - check_system_health: Overall system health check
    - get_agent_status: Get status of specific agent
    - get_regional_health: Get health of a region
    - get_tower_health: Get health of specific tower
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse input from Bedrock Agent action group format
    action_group = event.get('actionGroup', 'HealthMonitor')
    function_name = event.get('function', 'check_system_health')
    
    # Extract parameters from Bedrock Agent format
    parameters = {}
    if 'parameters' in event and isinstance(event['parameters'], list):
        for p in event['parameters']:
            parameters[p.get('name', '')] = p.get('value', '')
    elif 'parameters' in event and isinstance(event['parameters'], dict):
        parameters = event['parameters']
    
    # Route to appropriate handler
    handlers = {
        'check_system_health': check_system_health,
        'get_agent_status': get_agent_status,
        'get_regional_health': get_regional_health,
        'get_tower_health': get_tower_health,
    }
    
    handler = handlers.get(function_name, check_system_health)
    result = handler(parameters)
    
    # Format response for Bedrock Agent
    return format_bedrock_response(action_group, function_name, result)


def check_system_health(params: dict) -> dict:
    """Check overall system health across all components"""
    
    # Query agent status table
    table = dynamodb.Table(f'TRACE-AgentStatus-{ENVIRONMENT}')
    
    try:
        response = table.scan()
        agents = response.get('Items', [])
    except Exception as e:
        agents = []
    
    # Calculate health metrics
    total_agents = len(agents) if agents else 15  # Demo default
    healthy_agents = sum(1 for a in agents if a.get('status') == 'healthy')
    
    # Get CloudWatch metrics
    try:
        cw_response = cloudwatch.get_metric_statistics(
            Namespace='TRACE/Telemetry',
            MetricName='AnomalyCount',
            StartTime=datetime.utcnow() - timedelta(hours=1),
            EndTime=datetime.utcnow(),
            Period=3600,
            Statistics=['Sum']
        )
        anomaly_count = cw_response['Datapoints'][0]['Sum'] if cw_response['Datapoints'] else 0
    except:
        anomaly_count = 2  # Demo default
    
    # Calculate overall health score
    agent_health_score = (healthy_agents / total_agents * 100) if total_agents > 0 else 95
    anomaly_penalty = min(anomaly_count * 2, 20)
    health_score = max(0, agent_health_score - anomaly_penalty)
    
    # Determine status
    if health_score >= 90:
        status = 'healthy'
    elif health_score >= 70:
        status = 'degraded'
    else:
        status = 'critical'
    
    # Identify issues
    issues = []
    if anomaly_count > 5:
        issues.append({
            'type': 'high_anomaly_rate',
            'severity': 'warning',
            'message': f'{int(anomaly_count)} anomalies detected in the last hour'
        })
    
    unhealthy_agents = [a for a in agents if a.get('status') != 'healthy']
    for agent in unhealthy_agents[:3]:  # Top 3 issues
        issues.append({
            'type': 'agent_unhealthy',
            'severity': 'warning',
            'agent_id': agent.get('agent_id'),
            'message': f"Agent {agent.get('agent_id')} is {agent.get('status')}"
        })
    
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'overall_status': status,
        'health_score': round(health_score, 1),
        'components': {
            'agents': {
                'total': total_agents,
                'healthy': healthy_agents,
                'unhealthy': total_agents - healthy_agents
            },
            'infrastructure': {
                'status': 'healthy' if health_score > 70 else 'degraded',
                'active_regions': 5,
                'active_towers': 47
            }
        },
        'issues': issues,
        'recommendations': generate_recommendations(status, issues)
    }


def get_agent_status(params: dict) -> dict:
    """Get status of a specific agent"""
    
    agent_id = params.get('agent_id', 'principal-agent')
    
    table = dynamodb.Table(f'TRACE-AgentStatus-{ENVIRONMENT}')
    
    try:
        response = table.get_item(Key={'agent_id': agent_id})
        agent = response.get('Item', {})
    except Exception as e:
        agent = {}
    
    if not agent:
        # Return demo data
        agent = {
            'agent_id': agent_id,
            'status': 'healthy',
            'last_heartbeat': datetime.utcnow().isoformat(),
            'region_id': 'us-east-1',
            'type': 'edge',
            'uptime_hours': 72,
            'tasks_completed': 145,
            'error_rate': 0.02
        }
    
    return {
        'agent_id': agent_id,
        'status': agent.get('status', 'unknown'),
        'last_heartbeat': agent.get('last_heartbeat', datetime.utcnow().isoformat()),
        'region_id': agent.get('region_id', 'unknown'),
        'metrics': {
            'uptime_hours': agent.get('uptime_hours', 0),
            'tasks_completed': agent.get('tasks_completed', 0),
            'error_rate': agent.get('error_rate', 0)
        }
    }


def get_regional_health(params: dict) -> dict:
    """Get health status of a specific region"""
    
    region_id = params.get('region_id', 'R-E')
    
    # Query towers in region
    table = dynamodb.Table(f'TRACE-TowerConfig-{ENVIRONMENT}')
    
    try:
        response = table.query(
            IndexName='region-index',
            KeyConditionExpression='region_id = :rid',
            ExpressionAttributeValues={':rid': region_id}
        )
        towers = response.get('Items', [])
    except:
        towers = []
    
    # Calculate regional metrics
    total_towers = len(towers) if towers else 10
    healthy_towers = sum(1 for t in towers if t.get('status') == 'healthy')
    
    return {
        'region_id': region_id,
        'status': 'healthy' if healthy_towers / total_towers > 0.9 else 'degraded',
        'towers': {
            'total': total_towers,
            'healthy': healthy_towers,
            'degraded': total_towers - healthy_towers
        },
        'metrics': {
            'avg_utilization': 65.5,
            'total_users': 4500,
            'avg_latency_ms': 25
        }
    }


def get_tower_health(params: dict) -> dict:
    """Get health status of a specific tower"""
    
    tower_id = params.get('tower_id', 'TX001')
    
    # Query tower config
    table = dynamodb.Table(f'TRACE-TowerConfig-{ENVIRONMENT}')
    
    try:
        response = table.get_item(Key={'tower_id': tower_id})
        tower = response.get('Item', {})
    except:
        tower = {}
    
    if not tower:
        # Return demo data
        tower = {
            'tower_id': tower_id,
            'region_id': 'R-E',
            'status': 'healthy',
            'capacity': 1000,
            'connected_users': 456,
            'cpu_util_pct': 45,
            'bandwidth_utilization_pct': 52,
            'latency_ms': 18
        }
    
    return {
        'tower_id': tower_id,
        'region_id': tower.get('region_id', 'unknown'),
        'status': tower.get('status', 'unknown'),
        'metrics': {
            'capacity': tower.get('capacity', 0),
            'connected_users': tower.get('connected_users', 0),
            'utilization_pct': round(tower.get('connected_users', 0) / tower.get('capacity', 1) * 100, 1),
            'cpu_util_pct': tower.get('cpu_util_pct', 0),
            'bandwidth_utilization_pct': tower.get('bandwidth_utilization_pct', 0),
            'latency_ms': tower.get('latency_ms', 0)
        }
    }


def generate_recommendations(status: str, issues: list) -> list:
    """Generate recommendations based on health status and issues"""
    
    recommendations = []
    
    if status == 'critical':
        recommendations.append({
            'priority': 'high',
            'action': 'immediate_investigation',
            'description': 'System health is critical. Immediate investigation required.'
        })
    
    for issue in issues:
        if issue['type'] == 'high_anomaly_rate':
            recommendations.append({
                'priority': 'medium',
                'action': 'analyze_anomalies',
                'description': 'Review anomaly patterns and identify root causes.'
            })
        elif issue['type'] == 'agent_unhealthy':
            recommendations.append({
                'priority': 'medium',
                'action': 'restart_agent',
                'agent_id': issue.get('agent_id'),
                'description': f"Consider restarting agent {issue.get('agent_id')}"
            })
    
    if not recommendations:
        recommendations.append({
            'priority': 'low',
            'action': 'continue_monitoring',
            'description': 'System is healthy. Continue normal monitoring.'
        })
    
    return recommendations


def format_bedrock_response(action_group: str, function_name: str, result: dict) -> dict:
    """Format response for Bedrock Agent action group"""
    
    # Bedrock Agent expects this specific format
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'function': function_name,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(result, cls=DecimalEncoder)
                    }
                }
            }
        }
    }


def format_response(result: dict) -> dict:
    """Format response for Bedrock Agent action group"""
    
    # Bedrock Agent expects this specific format
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'HealthMonitor',
            'function': 'check_system_health',
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(result, cls=DecimalEncoder)
                    }
                }
            }
        }
    }
