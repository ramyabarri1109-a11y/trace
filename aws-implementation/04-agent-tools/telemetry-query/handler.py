"""
TRACE Telemetry Query Tool

This Lambda function provides telemetry querying capabilities for Bedrock Agents.
Queries data from Timestream and DynamoDB.
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize clients
dynamodb = boto3.resource('dynamodb')
timestream_query = boto3.client('timestream-query')

ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
TIMESTREAM_DATABASE = f'TRACE-Telemetry-{ENVIRONMENT}'


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event, context):
    """
    Telemetry Query Tool for Bedrock Agent
    
    Supported actions:
    - get_tower_metrics: Get current metrics for a tower
    - get_regional_metrics: Get aggregated metrics for a region
    - get_historical_data: Get historical telemetry data
    - analyze_trends: Analyze trends in metrics
    - get_anomalies: Get detected anomalies
    """
    
    action = event.get('action', 'get_tower_metrics')
    parameters = event.get('parameters', {})
    
    # Handle Bedrock action group format
    if 'actionGroup' in event:
        action = event.get('function', 'get_tower_metrics')
        parameters = {p['name']: p['value'] for p in event.get('parameters', [])}
    
    handlers = {
        'get_tower_metrics': get_tower_metrics,
        'get_regional_metrics': get_regional_metrics,
        'get_historical_data': get_historical_data,
        'analyze_trends': analyze_trends,
        'get_anomalies': get_anomalies,
    }
    
    handler = handlers.get(action, get_tower_metrics)
    result = handler(parameters)
    
    return format_response(result)


def get_tower_metrics(params: dict) -> dict:
    """Get current metrics for a specific tower"""
    
    tower_id = params.get('tower_id', 'TX001')
    
    # Try to query Timestream for recent data
    try:
        query = f"""
            SELECT tower_id, region_id,
                   AVG(connected_users) as avg_users,
                   AVG(cpu_util_pct) as avg_cpu,
                   AVG(bandwidth_utilization_pct) as avg_bandwidth,
                   AVG(latency_ms) as avg_latency,
                   MAX(connected_users) as max_users
            FROM "{TIMESTREAM_DATABASE}"."TowerMetrics"
            WHERE tower_id = '{tower_id}'
            AND time > ago(1h)
            GROUP BY tower_id, region_id
        """
        
        response = timestream_query.query(QueryString=query)
        rows = response.get('Rows', [])
        
        if rows:
            data = parse_timestream_row(rows[0], response['ColumnInfo'])
            return {
                'tower_id': tower_id,
                'source': 'timestream',
                'time_range': 'last_1_hour',
                'metrics': data
            }
    except Exception as e:
        print(f"Timestream query error: {str(e)}")
    
    # Fall back to demo data
    return {
        'tower_id': tower_id,
        'source': 'demo',
        'time_range': 'last_1_hour',
        'metrics': {
            'connected_users': 456,
            'capacity': 1000,
            'utilization_pct': 45.6,
            'cpu_util_pct': 52.3,
            'bandwidth_utilization_pct': 48.7,
            'latency_ms': 22,
            'packet_loss_pct': 0.3,
            'power_voltage_v': 48.2
        },
        'status': 'healthy',
        'last_updated': datetime.utcnow().isoformat()
    }


def get_regional_metrics(params: dict) -> dict:
    """Get aggregated metrics for a region"""
    
    region_id = params.get('region_id', 'R-E')
    
    # Try to query Timestream
    try:
        query = f"""
            SELECT region_id,
                   COUNT(DISTINCT tower_id) as tower_count,
                   SUM(connected_users) as total_users,
                   AVG(cpu_util_pct) as avg_cpu,
                   AVG(bandwidth_utilization_pct) as avg_bandwidth,
                   AVG(latency_ms) as avg_latency
            FROM "{TIMESTREAM_DATABASE}"."TowerMetrics"
            WHERE region_id = '{region_id}'
            AND time > ago(1h)
            GROUP BY region_id
        """
        
        response = timestream_query.query(QueryString=query)
        rows = response.get('Rows', [])
        
        if rows:
            data = parse_timestream_row(rows[0], response['ColumnInfo'])
            return {
                'region_id': region_id,
                'source': 'timestream',
                'time_range': 'last_1_hour',
                'metrics': data
            }
    except Exception as e:
        print(f"Timestream query error: {str(e)}")
    
    # Fall back to demo data
    return {
        'region_id': region_id,
        'source': 'demo',
        'time_range': 'last_1_hour',
        'metrics': {
            'tower_count': 10,
            'total_users': 4523,
            'total_capacity': 10000,
            'overall_utilization_pct': 45.2,
            'avg_cpu_util_pct': 48.5,
            'avg_bandwidth_util_pct': 52.1,
            'avg_latency_ms': 24,
            'anomaly_count': 2
        },
        'top_utilized_towers': [
            {'tower_id': 'TX003', 'utilization_pct': 82.5},
            {'tower_id': 'TX007', 'utilization_pct': 76.3},
            {'tower_id': 'TX001', 'utilization_pct': 68.9}
        ]
    }


def get_historical_data(params: dict) -> dict:
    """Get historical telemetry data"""
    
    tower_id = params.get('tower_id')
    region_id = params.get('region_id')
    hours = int(params.get('hours', 24))
    metric = params.get('metric', 'connected_users')
    
    # For demo, return simulated historical data
    data_points = []
    now = datetime.utcnow()
    
    for i in range(hours):
        timestamp = now - timedelta(hours=hours - i)
        # Simulate daily pattern
        hour = timestamp.hour
        base_value = 500
        if 8 <= hour <= 10 or 17 <= hour <= 19:
            multiplier = 1.5
        elif 0 <= hour <= 6:
            multiplier = 0.4
        else:
            multiplier = 1.0
        
        value = base_value * multiplier + (i % 5) * 10
        
        data_points.append({
            'timestamp': timestamp.isoformat(),
            'value': round(value, 1)
        })
    
    return {
        'tower_id': tower_id,
        'region_id': region_id,
        'metric': metric,
        'time_range_hours': hours,
        'data_points': data_points,
        'statistics': {
            'min': min(d['value'] for d in data_points),
            'max': max(d['value'] for d in data_points),
            'avg': round(sum(d['value'] for d in data_points) / len(data_points), 1)
        }
    }


def analyze_trends(params: dict) -> dict:
    """Analyze trends in metrics"""
    
    tower_id = params.get('tower_id')
    region_id = params.get('region_id', 'R-E')
    metric = params.get('metric', 'connected_users')
    
    # For demo, return simulated trend analysis
    return {
        'analysis_target': tower_id or region_id,
        'metric': metric,
        'trend': {
            'direction': 'increasing',
            'change_percent': 12.5,
            'period': 'last_24_hours'
        },
        'patterns': [
            {
                'pattern_type': 'daily_peak',
                'peak_hours': [9, 10, 17, 18],
                'confidence': 0.92
            },
            {
                'pattern_type': 'weekend_reduction',
                'reduction_percent': 25,
                'confidence': 0.85
            }
        ],
        'predictions': {
            'next_hour': {
                'predicted_value': 520,
                'confidence': 0.78
            },
            'next_peak': {
                'expected_time': '17:00',
                'predicted_value': 780,
                'confidence': 0.72
            }
        },
        'recommendations': [
            'Consider activating additional capacity at 16:30 to prepare for evening peak',
            'Current trend suggests 15% higher load than yesterday - monitor closely'
        ]
    }


def get_anomalies(params: dict) -> dict:
    """Get detected anomalies"""
    
    region_id = params.get('region_id')
    severity = params.get('severity', 'all')  # all, critical, warning
    hours = int(params.get('hours', 24))
    
    # Query DynamoDB for anomaly records
    # For demo, return simulated anomalies
    anomalies = [
        {
            'anomaly_id': 'ANM-001',
            'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            'tower_id': 'TX003',
            'region_id': 'R-E',
            'type': 'high_latency',
            'severity': 'warning',
            'value': 145,
            'threshold': 100,
            'status': 'resolved',
            'resolved_at': (datetime.utcnow() - timedelta(hours=1)).isoformat()
        },
        {
            'anomaly_id': 'ANM-002',
            'timestamp': (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
            'tower_id': 'TX007',
            'region_id': 'R-C',
            'type': 'near_capacity',
            'severity': 'warning',
            'value': 92,
            'threshold': 90,
            'status': 'active',
            'recommended_action': 'reroute_traffic'
        }
    ]
    
    # Filter by severity
    if severity != 'all':
        anomalies = [a for a in anomalies if a['severity'] == severity]
    
    # Filter by region
    if region_id:
        anomalies = [a for a in anomalies if a['region_id'] == region_id]
    
    return {
        'time_range_hours': hours,
        'region_filter': region_id,
        'severity_filter': severity,
        'total_count': len(anomalies),
        'active_count': sum(1 for a in anomalies if a['status'] == 'active'),
        'anomalies': anomalies
    }


def parse_timestream_row(row, column_info):
    """Parse a Timestream row into a dictionary"""
    result = {}
    for i, col in enumerate(column_info):
        name = col['Name']
        value = row['Data'][i].get('ScalarValue')
        if value:
            try:
                result[name] = float(value)
            except:
                result[name] = value
    return result


def format_response(result: dict) -> dict:
    """Format response for Bedrock Agent"""
    return {
        'statusCode': 200,
        'body': json.dumps(result, cls=DecimalEncoder)
    }
