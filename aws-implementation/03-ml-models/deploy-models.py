#!/usr/bin/env python3
"""
TRACE ML Models Deployment Script

Deploys SageMaker endpoints for traffic prediction and anomaly detection.
For demo purposes, we use Lambda-based inference. For production,
replace with actual SageMaker endpoints.
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


# Traffic Predictor Code
TRAFFIC_PREDICTOR_CODE = '''
"""
TRACE Traffic Predictor

Predicts traffic load and surge probability based on historical patterns.
This is a simplified rule-based model for demo purposes.
For production, replace with actual ML model (XGBoost, LSTM, etc.)
"""

import json
from datetime import datetime
import math

def lambda_handler(event, context):
    """
    Predict traffic load for a tower.
    
    Input:
    {
        "tower_id": "TX001",
        "current_users": 500,
        "capacity": 1000,
        "hour_of_day": 14,
        "day_of_week": 2,
        "historical_avg": 450
    }
    
    Output:
    {
        "tower_id": "TX001",
        "predicted_load": [520, 580, 610, 550],  # Next 4 hours
        "surge_probability": 0.35,
        "peak_hour": 16,
        "recommendation": "prepare_backup_capacity"
    }
    """
    
    body = event.get('body', event)
    if isinstance(body, str):
        body = json.loads(body)
    
    tower_id = body.get('tower_id', 'unknown')
    current_users = body.get('current_users', 0)
    capacity = body.get('capacity', 1000)
    hour = body.get('hour_of_day', datetime.now().hour)
    day = body.get('day_of_week', datetime.now().weekday())
    historical_avg = body.get('historical_avg', current_users)
    
    # Simple traffic pattern model
    # Peak hours: 8-10 AM, 12-2 PM, 5-8 PM
    hour_factors = {
        0: 0.3, 1: 0.2, 2: 0.15, 3: 0.1, 4: 0.1, 5: 0.2,
        6: 0.4, 7: 0.6, 8: 0.85, 9: 0.9, 10: 0.8, 11: 0.75,
        12: 0.9, 13: 0.85, 14: 0.7, 15: 0.65, 16: 0.75, 17: 0.95,
        18: 1.0, 19: 0.9, 20: 0.75, 21: 0.6, 22: 0.45, 23: 0.35
    }
    
    # Weekend factor
    weekend_factor = 0.85 if day >= 5 else 1.0
    
    # Predict next 4 hours
    predicted_load = []
    for h in range(1, 5):
        next_hour = (hour + h) % 24
        factor = hour_factors.get(next_hour, 0.5) * weekend_factor
        base_prediction = historical_avg * factor
        # Add some variance
        variance = base_prediction * 0.1 * (1 if h % 2 == 0 else -1)
        predicted_load.append(int(base_prediction + variance))
    
    # Calculate surge probability
    max_predicted = max(predicted_load)
    utilization = max_predicted / capacity if capacity > 0 else 0
    
    if utilization > 0.9:
        surge_probability = 0.85
    elif utilization > 0.8:
        surge_probability = 0.6
    elif utilization > 0.7:
        surge_probability = 0.35
    else:
        surge_probability = 0.1
    
    # Find peak hour
    peak_index = predicted_load.index(max(predicted_load))
    peak_hour = (hour + peak_index + 1) % 24
    
    # Recommendation
    if surge_probability > 0.7:
        recommendation = "activate_backup_cells"
    elif surge_probability > 0.5:
        recommendation = "prepare_backup_capacity"
    elif surge_probability > 0.3:
        recommendation = "monitor_closely"
    else:
        recommendation = "normal_operation"
    
    result = {
        'tower_id': tower_id,
        'predicted_load': predicted_load,
        'surge_probability': round(surge_probability, 2),
        'peak_hour': peak_hour,
        'max_predicted_utilization': round(utilization * 100, 1),
        'recommendation': recommendation,
        'confidence': 0.75  # Demo model confidence
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
'''


# Anomaly Detector Code
ANOMALY_DETECTOR_CODE = '''
"""
TRACE Anomaly Detector

Detects anomalies in tower telemetry data.
This is a simplified rule-based model for demo purposes.
For production, replace with Isolation Forest, Autoencoder, etc.
"""

import json
from datetime import datetime

def lambda_handler(event, context):
    """
    Detect anomalies in tower metrics.
    
    Input:
    {
        "tower_id": "TX001",
        "cpu_util_pct": 85,
        "latency_ms": 120,
        "packet_loss_pct": 2.5,
        "bandwidth_utilization_pct": 90,
        "connected_users": 950,
        "capacity": 1000,
        "rsrq_db": -12
    }
    
    Output:
    {
        "tower_id": "TX001",
        "anomaly_score": 0.75,
        "is_anomaly": true,
        "anomaly_types": ["high_latency", "packet_loss"],
        "severity": "warning",
        "recommended_action": "investigate_network_issues"
    }
    """
    
    body = event.get('body', event)
    if isinstance(body, str):
        body = json.loads(body)
    
    tower_id = body.get('tower_id', 'unknown')
    
    # Extract metrics with defaults
    cpu = body.get('cpu_util_pct', 50)
    latency = body.get('latency_ms', 20)
    packet_loss = body.get('packet_loss_pct', 0)
    bandwidth = body.get('bandwidth_utilization_pct', 50)
    users = body.get('connected_users', 500)
    capacity = body.get('capacity', 1000)
    rsrq = body.get('rsrq_db', -10)
    
    # Anomaly detection rules
    anomalies = []
    scores = []
    
    # CPU anomaly
    if cpu > 90:
        anomalies.append('critical_cpu')
        scores.append(0.9)
    elif cpu > 80:
        anomalies.append('high_cpu')
        scores.append(0.6)
    
    # Latency anomaly
    if latency > 150:
        anomalies.append('critical_latency')
        scores.append(0.85)
    elif latency > 100:
        anomalies.append('high_latency')
        scores.append(0.5)
    
    # Packet loss anomaly
    if packet_loss > 3:
        anomalies.append('severe_packet_loss')
        scores.append(0.8)
    elif packet_loss > 1:
        anomalies.append('packet_loss')
        scores.append(0.4)
    
    # Capacity anomaly
    utilization = users / capacity if capacity > 0 else 0
    if utilization > 0.95:
        anomalies.append('at_capacity')
        scores.append(0.9)
    elif utilization > 0.85:
        anomalies.append('near_capacity')
        scores.append(0.5)
    
    # Signal quality anomaly
    if rsrq < -15:
        anomalies.append('poor_signal_quality')
        scores.append(0.6)
    
    # Calculate overall anomaly score
    if scores:
        anomaly_score = max(scores)
    else:
        anomaly_score = 0.1
    
    # Determine severity
    if anomaly_score > 0.8:
        severity = 'critical'
    elif anomaly_score > 0.5:
        severity = 'warning'
    elif anomaly_score > 0.3:
        severity = 'info'
    else:
        severity = 'normal'
    
    # Recommended action
    if 'critical_cpu' in anomalies or 'at_capacity' in anomalies:
        recommended_action = 'immediate_load_balancing'
    elif 'severe_packet_loss' in anomalies or 'critical_latency' in anomalies:
        recommended_action = 'investigate_network_issues'
    elif any('high' in a or 'near' in a for a in anomalies):
        recommended_action = 'monitor_and_prepare'
    else:
        recommended_action = 'continue_monitoring'
    
    result = {
        'tower_id': tower_id,
        'anomaly_score': round(anomaly_score, 2),
        'is_anomaly': anomaly_score > 0.4,
        'anomaly_types': anomalies,
        'severity': severity,
        'recommended_action': recommended_action,
        'timestamp': datetime.utcnow().isoformat(),
        'metrics_analyzed': {
            'cpu': cpu,
            'latency': latency,
            'packet_loss': packet_loss,
            'utilization': round(utilization * 100, 1)
        }
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
'''


def create_lambda_function(function_name: str, code: str, description: str):
    """Create a Lambda function from code string"""
    
    infra = load_infrastructure_outputs()
    account_id = get_account_id()
    role_arn = infra.get('iam', {}).get('LambdaRoleArn',
                f'arn:aws:iam::{account_id}:role/TRACE-Lambda-Role-{ENVIRONMENT}')
    
    # Create zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        zip_path = tmp.name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('handler.py', code)
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    full_name = f'TRACE-{function_name}-{ENVIRONMENT}'
    
    try:
        # Try to update existing function
        lambda_client.update_function_code(
            FunctionName=full_name,
            ZipFile=zip_content
        )
        print(f"  Updated: {full_name}")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        lambda_client.create_function(
            FunctionName=full_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': zip_content},
            Description=description,
            Timeout=30,
            MemorySize=256,
            Environment={
                'Variables': {
                    'ENVIRONMENT': ENVIRONMENT
                }
            },
            Tags={
                'Project': 'TRACE',
                'Environment': ENVIRONMENT,
                'Type': 'MLModel'
            }
        )
        print(f"  Created: {full_name}")
    
    # Clean up
    os.unlink(zip_path)
    
    return full_name


def main():
    print("=" * 60)
    print("TRACE ML Models Deployment")
    print("=" * 60)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    print()
    print("Note: Using Lambda-based inference for demo purposes.")
    print("For production, deploy actual ML models to SageMaker.")
    print()
    
    # Deploy Traffic Predictor
    print("🔮 Deploying Traffic Predictor...")
    create_lambda_function(
        'TrafficPredictor',
        TRAFFIC_PREDICTOR_CODE,
        'TRACE Traffic Predictor - Forecasts traffic load and surge probability'
    )
    
    # Deploy Anomaly Detector
    print("\n🔍 Deploying Anomaly Detector...")
    create_lambda_function(
        'AnomalyDetector',
        ANOMALY_DETECTOR_CODE,
        'TRACE Anomaly Detector - Detects anomalies in tower metrics'
    )
    
    print("\n" + "=" * 60)
    print("✅ ML Models Deployment Complete!")
    print("=" * 60)
    print("\nDeployed functions:")
    print(f"  • TRACE-TrafficPredictor-{ENVIRONMENT}")
    print(f"  • TRACE-AnomalyDetector-{ENVIRONMENT}")
    print("\nNext step: Run 04-agent-tools/deploy-tools.py")


if __name__ == '__main__':
    main()
