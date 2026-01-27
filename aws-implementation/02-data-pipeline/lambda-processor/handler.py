"""
TRACE Telemetry Processor Lambda

This Lambda function processes incoming telemetry data from Kinesis,
stores it in Timestream and DynamoDB, and publishes CloudWatch metrics.
"""

import json
import base64
import boto3
import os
from datetime import datetime
from decimal import Decimal

# Initialize clients
dynamodb = boto3.resource('dynamodb')
timestream_write = boto3.client('timestream-write')
cloudwatch = boto3.client('cloudwatch')

# Configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
TIMESTREAM_DATABASE = os.getenv('TIMESTREAM_DATABASE', f'TRACE-Telemetry-{ENVIRONMENT}')
TIMESTREAM_TABLE = os.getenv('TIMESTREAM_TABLE', 'TowerMetrics')
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE', f'TRACE-TelemetryAggregates-{ENVIRONMENT}')


def lambda_handler(event, context):
    """
    Process Kinesis records containing tower telemetry data.
    """
    processed_count = 0
    error_count = 0
    
    records_for_timestream = []
    metrics_for_cloudwatch = []
    
    for record in event['Records']:
        try:
            # Decode Kinesis record
            payload = base64.b64decode(record['kinesis']['data'])
            telemetry = json.loads(payload)
            
            # Process the telemetry record
            processed = process_telemetry(telemetry)
            
            # Prepare for Timestream
            timestream_record = create_timestream_record(processed)
            records_for_timestream.append(timestream_record)
            
            # Prepare CloudWatch metrics
            cw_metrics = create_cloudwatch_metrics(processed)
            metrics_for_cloudwatch.extend(cw_metrics)
            
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            error_count += 1
    
    # Batch write to Timestream
    if records_for_timestream:
        write_to_timestream(records_for_timestream)
    
    # Publish CloudWatch metrics
    if metrics_for_cloudwatch:
        publish_cloudwatch_metrics(metrics_for_cloudwatch)
    
    # Update aggregates in DynamoDB
    update_aggregates(event['Records'])
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed_count,
            'errors': error_count
        })
    }


def process_telemetry(telemetry: dict) -> dict:
    """
    Process and enrich telemetry data.
    """
    # Add processing timestamp
    telemetry['processed_at'] = datetime.utcnow().isoformat()
    
    # Calculate derived metrics
    if 'connected_users' in telemetry and 'capacity_users' in telemetry:
        capacity = telemetry['capacity_users']
        if capacity > 0:
            telemetry['utilization_pct'] = (telemetry['connected_users'] / capacity) * 100
    
    # Detect anomalies
    telemetry['anomaly_flags'] = detect_anomalies(telemetry)
    
    return telemetry


def detect_anomalies(telemetry: dict) -> list:
    """
    Detect anomalies in telemetry data.
    """
    anomalies = []
    
    # High CPU usage
    if telemetry.get('cpu_util_pct', 0) > 85:
        anomalies.append('high_cpu')
    
    # High latency
    if telemetry.get('latency_ms', 0) > 100:
        anomalies.append('high_latency')
    
    # Packet loss
    if telemetry.get('packet_loss_pct', 0) > 1:
        anomalies.append('packet_loss')
    
    # Low RSRQ (signal quality)
    if telemetry.get('rsrq_db', 0) < -15:
        anomalies.append('poor_signal_quality')
    
    # Overloaded tower
    if telemetry.get('utilization_pct', 0) > 90:
        anomalies.append('near_capacity')
    
    return anomalies


def create_timestream_record(telemetry: dict) -> dict:
    """
    Create a Timestream record from telemetry data.
    """
    timestamp = telemetry.get('timestamp', datetime.utcnow().isoformat())
    
    # Parse timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace('+00:00', ''))
        time_value = str(int(dt.timestamp() * 1000))
    except:
        time_value = str(int(datetime.utcnow().timestamp() * 1000))
    
    dimensions = [
        {'Name': 'tower_id', 'Value': str(telemetry.get('tower_id', 'unknown'))},
        {'Name': 'region_id', 'Value': str(telemetry.get('region_id', 'unknown'))},
        {'Name': 'agent_id', 'Value': str(telemetry.get('agent_id', 'unknown'))},
    ]
    
    # Create multi-measure record
    measure_values = [
        {'Name': 'connected_users', 'Value': str(telemetry.get('connected_users', 0)), 'Type': 'BIGINT'},
        {'Name': 'cpu_util_pct', 'Value': str(telemetry.get('cpu_util_pct', 0)), 'Type': 'DOUBLE'},
        {'Name': 'bandwidth_utilization_pct', 'Value': str(telemetry.get('bandwidth_utilization_pct', 0)), 'Type': 'DOUBLE'},
        {'Name': 'latency_ms', 'Value': str(telemetry.get('latency_ms', 0)), 'Type': 'BIGINT'},
        {'Name': 'packet_loss_pct', 'Value': str(telemetry.get('packet_loss_pct', 0)), 'Type': 'DOUBLE'},
        {'Name': 'power_voltage_v', 'Value': str(telemetry.get('power_voltage_v', 0)), 'Type': 'DOUBLE'},
    ]
    
    return {
        'Dimensions': dimensions,
        'MeasureName': 'tower_metrics',
        'MeasureValueType': 'MULTI',
        'MeasureValues': measure_values,
        'Time': time_value,
        'TimeUnit': 'MILLISECONDS'
    }


def write_to_timestream(records: list):
    """
    Write records to Timestream in batches.
    """
    # Timestream accepts max 100 records per write
    batch_size = 100
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        try:
            timestream_write.write_records(
                DatabaseName=TIMESTREAM_DATABASE,
                TableName=TIMESTREAM_TABLE,
                Records=batch,
                CommonAttributes={}
            )
            print(f"Wrote {len(batch)} records to Timestream")
        except timestream_write.exceptions.RejectedRecordsException as e:
            print(f"Some records rejected: {e.response['RejectedRecords']}")
        except Exception as e:
            print(f"Error writing to Timestream: {str(e)}")


def create_cloudwatch_metrics(telemetry: dict) -> list:
    """
    Create CloudWatch metrics from telemetry data.
    """
    tower_id = telemetry.get('tower_id', 'unknown')
    region_id = telemetry.get('region_id', 'unknown')
    
    metrics = []
    
    # Add metrics
    metric_mappings = [
        ('ConnectedUsers', 'connected_users', 'Count'),
        ('CPUUtilization', 'cpu_util_pct', 'Percent'),
        ('BandwidthUtilization', 'bandwidth_utilization_pct', 'Percent'),
        ('Latency', 'latency_ms', 'Milliseconds'),
        ('PacketLoss', 'packet_loss_pct', 'Percent'),
    ]
    
    for metric_name, field, unit in metric_mappings:
        if field in telemetry:
            metrics.append({
                'MetricName': metric_name,
                'Dimensions': [
                    {'Name': 'TowerId', 'Value': tower_id},
                    {'Name': 'RegionId', 'Value': region_id},
                ],
                'Value': float(telemetry[field]),
                'Unit': unit
            })
    
    # Add anomaly count metric
    anomaly_count = len(telemetry.get('anomaly_flags', []))
    metrics.append({
        'MetricName': 'AnomalyCount',
        'Dimensions': [
            {'Name': 'TowerId', 'Value': tower_id},
            {'Name': 'RegionId', 'Value': region_id},
        ],
        'Value': anomaly_count,
        'Unit': 'Count'
    })
    
    return metrics


def publish_cloudwatch_metrics(metrics: list):
    """
    Publish metrics to CloudWatch in batches.
    """
    # CloudWatch accepts max 1000 metrics per call
    batch_size = 1000
    
    for i in range(0, len(metrics), batch_size):
        batch = metrics[i:i + batch_size]
        
        try:
            cloudwatch.put_metric_data(
                Namespace='TRACE/Telemetry',
                MetricData=batch
            )
            print(f"Published {len(batch)} metrics to CloudWatch")
        except Exception as e:
            print(f"Error publishing to CloudWatch: {str(e)}")


def update_aggregates(records: list):
    """
    Update hourly aggregates in DynamoDB for faster querying.
    """
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    # Group by tower and hour
    aggregates = {}
    
    for record in records:
        try:
            payload = base64.b64decode(record['kinesis']['data'])
            telemetry = json.loads(payload)
            
            tower_id = telemetry.get('tower_id', 'unknown')
            timestamp = telemetry.get('timestamp', datetime.utcnow().isoformat())
            
            # Get hour key
            try:
                dt = datetime.fromisoformat(timestamp.replace('+00:00', ''))
                hour_key = dt.strftime('%Y-%m-%dT%H:00:00')
            except:
                hour_key = datetime.utcnow().strftime('%Y-%m-%dT%H:00:00')
            
            key = f"{tower_id}#{hour_key}"
            
            if key not in aggregates:
                aggregates[key] = {
                    'count': 0,
                    'total_users': 0,
                    'total_cpu': 0,
                    'max_latency': 0,
                    'anomaly_count': 0
                }
            
            aggregates[key]['count'] += 1
            aggregates[key]['total_users'] += telemetry.get('connected_users', 0)
            aggregates[key]['total_cpu'] += telemetry.get('cpu_util_pct', 0)
            aggregates[key]['max_latency'] = max(
                aggregates[key]['max_latency'],
                telemetry.get('latency_ms', 0)
            )
            
        except Exception as e:
            print(f"Error aggregating record: {str(e)}")
    
    # Write aggregates to DynamoDB
    for key, agg in aggregates.items():
        tower_id, hour_key = key.split('#')
        
        try:
            table.update_item(
                Key={
                    'partition_key': tower_id,
                    'timestamp_hour': hour_key
                },
                UpdateExpression="""
                    SET record_count = if_not_exists(record_count, :zero) + :count,
                        total_users = if_not_exists(total_users, :zero) + :users,
                        total_cpu = if_not_exists(total_cpu, :zero) + :cpu,
                        max_latency = if_not_exists(max_latency, :zero),
                        updated_at = :now,
                        #ttl = :ttl
                """,
                ExpressionAttributeNames={
                    '#ttl': 'ttl'
                },
                ExpressionAttributeValues={
                    ':zero': 0,
                    ':count': agg['count'],
                    ':users': agg['total_users'],
                    ':cpu': Decimal(str(agg['total_cpu'])),
                    ':now': datetime.utcnow().isoformat(),
                    ':ttl': int((datetime.utcnow().timestamp()) + (30 * 24 * 60 * 60))  # 30 days
                }
            )
        except Exception as e:
            print(f"Error updating aggregate: {str(e)}")
