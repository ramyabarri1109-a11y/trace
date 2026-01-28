"""
TRACE MCP Lambda Functions

These Lambda functions implement MCP-style tools that can be invoked by
Amazon Bedrock agents or called directly via API Gateway.
"""

import json
import boto3
import random
from datetime import datetime
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Main Lambda handler - routes to appropriate MCP tool
    
    Event format:
    {
        "tool": "get_tower_telemetry",
        "parameters": {
            "tower_id": "tower-001"
        }
    }
    """
    tool = event.get('tool', '')
    parameters = event.get('parameters', {})
    
    # Route to appropriate handler
    handlers = {
        # Telemetry tools
        'get_tower_telemetry': get_tower_telemetry,
        'detect_tower_anomalies': detect_tower_anomalies,
        'get_network_health_summary': get_network_health_summary,
        'get_power_consumption_report': get_power_consumption_report,
        
        # Tower config tools
        'get_tower_config': get_tower_config,
        'set_power_mode': set_power_mode,
        'set_active_trx': set_active_trx,
        'activate_warm_spare': activate_warm_spare,
        
        # Energy tools
        'get_energy_status': get_energy_status,
        'get_energy_recommendations': get_energy_recommendations,
        'execute_energy_optimization': execute_energy_optimization,
        
        # Policy tools
        'get_policy': get_policy,
        'execute_remediation': execute_remediation,
        'get_remediation_status': get_remediation_status,
    }
    
    handler = handlers.get(tool)
    if handler:
        try:
            result = handler(parameters)
            return {
                'statusCode': 200,
                'body': json.dumps(result, cls=DecimalEncoder)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Unknown tool: {tool}'})
        }


# ============================================
# TELEMETRY TOOLS
# ============================================

def get_tower_telemetry(params):
    """Get real-time telemetry metrics for towers"""
    tower_id = params.get('tower_id')
    
    towers = ["tower-001", "tower-002", "tower-003", "tower-004", "tower-005"]
    if tower_id:
        towers = [tower_id]
    
    metrics = {}
    for tid in towers:
        metrics[tid] = {
            "tower_id": tid,
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": round(random.uniform(20, 85), 2),
            "memory_usage": round(random.uniform(30, 90), 2),
            "latency_ms": round(random.uniform(5, 150), 2),
            "active_connections": random.randint(50, 500),
            "bandwidth_mbps": round(random.uniform(100, 1000), 2),
            "power_consumption_kw": round(random.uniform(2, 10), 2),
            "temperature_celsius": round(random.uniform(25, 65), 2),
            "signal_strength_dbm": round(random.uniform(-90, -50), 2),
            "packet_loss_percent": round(random.uniform(0, 5), 2),
            "status": random.choice(["healthy", "healthy", "healthy", "warning", "critical"])
        }
    
    return metrics


def detect_tower_anomalies(params):
    """Detect anomalies in tower metrics"""
    tower_id = params.get('tower_id')
    metrics = get_tower_telemetry({'tower_id': tower_id})
    
    anomalies = []
    for tid, data in metrics.items():
        if data["cpu_usage"] > 80:
            anomalies.append({
                "tower_id": tid,
                "type": "HIGH_CPU",
                "severity": "warning" if data["cpu_usage"] < 90 else "critical",
                "value": data["cpu_usage"],
                "threshold": 80,
                "message": f"CPU usage at {data['cpu_usage']}%"
            })
        
        if data["latency_ms"] > 100:
            anomalies.append({
                "tower_id": tid,
                "type": "HIGH_LATENCY",
                "severity": "warning" if data["latency_ms"] < 150 else "critical",
                "value": data["latency_ms"],
                "threshold": 100
            })
        
        if data["power_consumption_kw"] > 8:
            anomalies.append({
                "tower_id": tid,
                "type": "HIGH_POWER",
                "severity": "warning",
                "value": data["power_consumption_kw"],
                "threshold": 8
            })
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_anomalies": len(anomalies),
        "anomalies": anomalies
    }


def get_network_health_summary(params):
    """Get overall network health summary"""
    metrics = get_tower_telemetry({})
    
    statuses = [m["status"] for m in metrics.values()]
    return {
        "timestamp": datetime.now().isoformat(),
        "total_towers": len(metrics),
        "healthy": statuses.count("healthy"),
        "warning": statuses.count("warning"),
        "critical": statuses.count("critical"),
        "avg_cpu_usage": round(sum(m["cpu_usage"] for m in metrics.values()) / len(metrics), 2),
        "avg_latency_ms": round(sum(m["latency_ms"] for m in metrics.values()) / len(metrics), 2),
        "total_power_kw": round(sum(m["power_consumption_kw"] for m in metrics.values()), 2),
        "total_connections": sum(m["active_connections"] for m in metrics.values())
    }


def get_power_consumption_report(params):
    """Get power consumption report with recommendations"""
    metrics = get_tower_telemetry({})
    include_recommendations = params.get('include_recommendations', True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "towers": []
    }
    
    total_power = 0
    for tower_id, data in metrics.items():
        tower_report = {
            "tower_id": tower_id,
            "current_power_kw": data["power_consumption_kw"],
            "load_percent": round(data["active_connections"] / 5, 1),
            "efficiency_score": round(100 - (data["power_consumption_kw"] * 10 / max(data["active_connections"], 1)), 2)
        }
        
        if include_recommendations:
            if data["active_connections"] < 100 and data["power_consumption_kw"] > 5:
                tower_report["recommendation"] = "LOW_LOAD_HIGH_POWER - Consider TRX shutdown"
                tower_report["potential_savings_kw"] = round(data["power_consumption_kw"] * 0.3, 2)
            elif data["active_connections"] < 200:
                tower_report["recommendation"] = "MODERATE_LOAD - Enable power saving mode"
                tower_report["potential_savings_kw"] = round(data["power_consumption_kw"] * 0.15, 2)
            else:
                tower_report["recommendation"] = "OPTIMAL - No action needed"
                tower_report["potential_savings_kw"] = 0
        
        total_power += data["power_consumption_kw"]
        report["towers"].append(tower_report)
    
    report["total_power_kw"] = round(total_power, 2)
    if include_recommendations:
        report["total_potential_savings_kw"] = round(
            sum(t.get("potential_savings_kw", 0) for t in report["towers"]), 2
        )
        report["potential_savings_percent"] = round(
            report["total_potential_savings_kw"] / total_power * 100, 1
        ) if total_power > 0 else 0
    
    return report


# ============================================
# TOWER CONFIG TOOLS
# ============================================

TOWER_CONFIGS = {
    "tower-001": {"tower_id": "tower-001", "name": "Downtown Tower A", "region": "region-a", "trx_count": 4, "active_trx": 4, "power_mode": "normal"},
    "tower-002": {"tower_id": "tower-002", "name": "Uptown Tower B", "region": "region-a", "trx_count": 3, "active_trx": 3, "power_mode": "normal"},
    "tower-003": {"tower_id": "tower-003", "name": "Harbor Tower C", "region": "region-b", "trx_count": 5, "active_trx": 4, "power_mode": "eco"},
    "tower-004": {"tower_id": "tower-004", "name": "Industrial Tower D", "region": "region-b", "trx_count": 3, "active_trx": 2, "power_mode": "eco"},
    "tower-005": {"tower_id": "tower-005", "name": "Suburban Tower E", "region": "region-a", "trx_count": 4, "active_trx": 3, "power_mode": "normal"},
}


def get_tower_config(params):
    """Get tower configuration"""
    tower_id = params.get('tower_id')
    if tower_id:
        return TOWER_CONFIGS.get(tower_id, {"error": f"Tower {tower_id} not found"})
    return TOWER_CONFIGS


def set_power_mode(params):
    """Set tower power mode"""
    tower_id = params.get('tower_id')
    power_mode = params.get('power_mode')
    
    if tower_id not in TOWER_CONFIGS:
        return {"error": f"Tower {tower_id} not found"}
    
    old_mode = TOWER_CONFIGS[tower_id]["power_mode"]
    TOWER_CONFIGS[tower_id]["power_mode"] = power_mode
    
    # Log to DynamoDB
    try:
        table = dynamodb.Table('trace-remediation-log')
        table.put_item(Item={
            'id': f"PWR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{tower_id}",
            'tower_id': tower_id,
            'action': 'set_power_mode',
            'old_value': old_mode,
            'new_value': power_mode,
            'timestamp': datetime.now().isoformat()
        })
    except Exception:
        pass  # Continue even if logging fails
    
    return {
        "success": True,
        "tower_id": tower_id,
        "previous_mode": old_mode,
        "new_mode": power_mode,
        "timestamp": datetime.now().isoformat(),
        "estimated_power_change_percent": {"normal": 0, "eco": -30, "boost": 20, "standby": -70}.get(power_mode, 0)
    }


def set_active_trx(params):
    """Set number of active TRX on a tower"""
    tower_id = params.get('tower_id')
    active_trx_count = params.get('active_trx_count')
    
    if tower_id not in TOWER_CONFIGS:
        return {"error": f"Tower {tower_id} not found"}
    
    config = TOWER_CONFIGS[tower_id]
    max_trx = config["trx_count"]
    
    if active_trx_count < 1 or active_trx_count > max_trx:
        return {"error": f"active_trx_count must be between 1 and {max_trx}"}
    
    old_count = config["active_trx"]
    config["active_trx"] = active_trx_count
    
    return {
        "success": True,
        "tower_id": tower_id,
        "previous_active_trx": old_count,
        "new_active_trx": active_trx_count,
        "max_trx": max_trx,
        "power_savings_percent": round((old_count - active_trx_count) / old_count * 25, 1) if old_count > active_trx_count else 0,
        "timestamp": datetime.now().isoformat()
    }


def activate_warm_spare(params):
    """Activate warm spare capacity for traffic surge"""
    tower_id = params.get('tower_id')
    reason = params.get('reason', 'traffic_surge')
    
    if tower_id not in TOWER_CONFIGS:
        return {"error": f"Tower {tower_id} not found"}
    
    config = TOWER_CONFIGS[tower_id]
    old_trx = config["active_trx"]
    old_mode = config["power_mode"]
    
    config["active_trx"] = config["trx_count"]
    config["power_mode"] = "boost"
    
    return {
        "success": True,
        "tower_id": tower_id,
        "reason": reason,
        "changes": {
            "active_trx": {"from": old_trx, "to": config["trx_count"]},
            "power_mode": {"from": old_mode, "to": "boost"}
        },
        "capacity_increase_percent": round((config["trx_count"] - old_trx) / config["trx_count"] * 100, 1),
        "timestamp": datetime.now().isoformat()
    }


# ============================================
# ENERGY TOOLS
# ============================================

ENERGY_STATE = {
    "mode": "normal",
    "total_savings_kwh": 0
}


def get_energy_status(params):
    """Get current energy status"""
    hour = datetime.now().hour
    
    if 1 <= hour <= 6:
        traffic_level = "low"
        traffic_percent = random.uniform(10, 30)
    elif (8 <= hour <= 10) or (17 <= hour <= 20):
        traffic_level = "high"
        traffic_percent = random.uniform(70, 95)
    else:
        traffic_level = "medium"
        traffic_percent = random.uniform(40, 65)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "network_energy_mode": ENERGY_STATE["mode"],
        "current_traffic_level": traffic_level,
        "traffic_percent": round(traffic_percent, 1),
        "total_savings_kwh": ENERGY_STATE["total_savings_kwh"],
        "recommendation": "Energy savings available" if traffic_level == "low" else "Normal operations"
    }


def get_energy_recommendations(params):
    """Get energy optimization recommendations"""
    tower_id = params.get('tower_id')
    status = get_energy_status({})
    traffic_level = status["current_traffic_level"]
    
    recommendations = {
        "timestamp": datetime.now().isoformat(),
        "traffic_level": traffic_level,
        "recommendations": []
    }
    
    if traffic_level == "low":
        recommendations["recommendations"] = [
            {"action": "reduce_trx", "description": "Reduce TRX to minimum", "savings_percent": 40},
            {"action": "enable_eco_mode", "description": "Enable ECO power mode", "savings_percent": 20},
            {"action": "reduce_antenna_power", "description": "Lower transmission power", "savings_percent": 15}
        ]
        recommendations["total_potential_savings_percent"] = 60
    elif traffic_level == "medium":
        recommendations["recommendations"] = [
            {"action": "optimize_trx", "description": "Match TRX to demand", "savings_percent": 20},
            {"action": "enable_eco_mode", "description": "Enable ECO power mode", "savings_percent": 15}
        ]
        recommendations["total_potential_savings_percent"] = 30
    else:
        recommendations["recommendations"] = [
            {"action": "maintain_capacity", "description": "Keep full capacity for peak demand", "savings_percent": 0}
        ]
        recommendations["total_potential_savings_percent"] = 0
    
    return recommendations


def execute_energy_optimization(params):
    """Execute an energy optimization action"""
    tower_id = params.get('tower_id')
    action = params.get('action')
    
    action_savings = {
        "reduce_trx": 2.5,
        "enable_eco_mode": 1.5,
        "reduce_antenna_power": 1.0,
        "optimize_trx": 1.8,
        "restore_normal": 0
    }
    
    savings = action_savings.get(action, 0)
    ENERGY_STATE["total_savings_kwh"] += savings
    
    return {
        "success": True,
        "tower_id": tower_id,
        "action": action,
        "power_savings_kw": savings,
        "total_network_savings_kwh": ENERGY_STATE["total_savings_kwh"],
        "timestamp": datetime.now().isoformat()
    }


# ============================================
# POLICY & REMEDIATION TOOLS
# ============================================

POLICIES = {
    "HIGH_CPU": {
        "policy_id": "POL-001",
        "name": "High CPU Remediation",
        "actions": ["scale_resources", "load_balance", "restart_services"],
        "timeout_seconds": 300
    },
    "HIGH_LATENCY": {
        "policy_id": "POL-002",
        "name": "High Latency Remediation",
        "actions": ["optimize_routing", "increase_bandwidth", "activate_spare"],
        "timeout_seconds": 180
    },
    "CONGESTION": {
        "policy_id": "POL-004",
        "name": "Traffic Congestion Remediation",
        "actions": ["activate_trx", "boost_power", "load_balance"],
        "timeout_seconds": 120
    },
    "HIGH_POWER": {
        "policy_id": "POL-005",
        "name": "High Power Consumption Remediation",
        "actions": ["enable_eco_mode", "reduce_trx", "lower_antenna_power"],
        "timeout_seconds": 600
    }
}

REMEDIATION_LOG = []


def get_policy(params):
    """Get remediation policy"""
    issue_type = params.get('issue_type')
    if issue_type:
        return POLICIES.get(issue_type, {"error": f"Unknown policy: {issue_type}"})
    return POLICIES


def execute_remediation(params):
    """Execute a remediation policy"""
    issue_type = params.get('issue_type')
    tower_id = params.get('tower_id')
    
    if issue_type not in POLICIES:
        return {"error": f"Unknown issue type: {issue_type}"}
    
    policy = POLICIES[issue_type]
    remediation_id = f"REM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{tower_id}"
    
    remediation = {
        "remediation_id": remediation_id,
        "issue_type": issue_type,
        "tower_id": tower_id,
        "policy_applied": policy["policy_id"],
        "status": "in_progress",
        "actions_to_execute": policy["actions"],
        "started_at": datetime.now().isoformat()
    }
    
    REMEDIATION_LOG.append(remediation)
    
    # Log to DynamoDB
    try:
        table = dynamodb.Table('trace-remediation-log')
        table.put_item(Item={
            'id': remediation_id,
            'tower_id': tower_id,
            'issue_type': issue_type,
            'policy_id': policy["policy_id"],
            'status': 'in_progress',
            'timestamp': datetime.now().isoformat()
        })
    except Exception:
        pass
    
    return remediation


def get_remediation_status(params):
    """Get status of a remediation"""
    remediation_id = params.get('remediation_id')
    
    for rem in REMEDIATION_LOG:
        if rem["remediation_id"] == remediation_id:
            return rem
    
    return {"error": f"Remediation {remediation_id} not found"}
