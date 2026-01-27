#!/usr/bin/env python3
"""
TRACE Demo Simulation Script
Simulates telemetry data and agent interactions for demonstration.
"""

import json
import time
import random
import boto3
from datetime import datetime, timedelta

# Configuration
REGION = "us-east-1"
KINESIS_STREAM = "trace-telemetry-stream"

# Initialize clients
kinesis = boto3.client("kinesis", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)


def generate_tower_telemetry(tower_id: str, region: str, healthy: bool = True):
    """Generate realistic tower telemetry data."""
    
    base_metrics = {
        "cpu_percent": random.uniform(40, 60),
        "memory_percent": random.uniform(50, 70),
        "latency_ms": random.uniform(20, 50),
        "connected_users": random.randint(200, 600),
        "trx_active": random.randint(4, 8),
        "trx_total": 8,
        "energy_kwh": random.uniform(15, 25),
        "traffic_gbps": random.uniform(2.0, 5.0),
    }
    
    if not healthy:
        # Simulate degraded conditions
        anomaly = random.choice(["high_latency", "high_cpu", "high_users", "low_energy"])
        if anomaly == "high_latency":
            base_metrics["latency_ms"] = random.uniform(150, 300)
        elif anomaly == "high_cpu":
            base_metrics["cpu_percent"] = random.uniform(85, 98)
        elif anomaly == "high_users":
            base_metrics["connected_users"] = random.randint(900, 1100)
        elif anomaly == "low_energy":
            base_metrics["trx_active"] = 2  # Low activity, can optimize
    
    return {
        "tower_id": tower_id,
        "region": region,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metrics": base_metrics,
        "status": "healthy" if healthy else "degraded",
    }


def generate_agent_state(agent_id: str, agent_type: str, healthy: bool = True):
    """Generate agent state data."""
    return {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "status": "active" if healthy else "degraded",
        "last_heartbeat": datetime.utcnow().isoformat() + "Z",
        "task_count": random.randint(10, 100),
        "success_rate": random.uniform(0.95, 0.99) if healthy else random.uniform(0.60, 0.80),
        "current_task": random.choice([None, "monitoring", "analyzing", "executing"]),
    }


def send_to_kinesis(records: list):
    """Send records to Kinesis stream."""
    try:
        kinesis_records = [
            {
                "Data": json.dumps(record).encode(),
                "PartitionKey": record.get("tower_id", record.get("agent_id", "default"))
            }
            for record in records
        ]
        
        response = kinesis.put_records(
            StreamName=KINESIS_STREAM,
            Records=kinesis_records
        )
        
        failed = response.get("FailedRecordCount", 0)
        print(f"  📤 Sent {len(records) - failed}/{len(records)} records to Kinesis")
        return failed == 0
    except Exception as e:
        print(f"  ❌ Kinesis error: {e}")
        return False


def update_dynamodb_tower(tower_data: dict):
    """Update tower configuration in DynamoDB."""
    try:
        table = dynamodb.Table("trace-tower-config")
        table.put_item(Item={
            "tower_id": tower_data["tower_id"],
            "region": tower_data["region"],
            "status": tower_data["status"],
            "last_updated": tower_data["timestamp"],
            "metrics": tower_data["metrics"],
        })
        return True
    except Exception as e:
        print(f"  ⚠️ DynamoDB update failed: {e}")
        return False


def run_simulation(duration_seconds: int = 60, interval: float = 5.0):
    """Run telemetry simulation for specified duration."""
    
    # Tower configuration
    towers = [
        {"id": "TX001", "region": "R-N"},
        {"id": "TX002", "region": "R-N"},
        {"id": "TX003", "region": "R-S"},
        {"id": "TX004", "region": "R-S"},
        {"id": "TX005", "region": "R-E"},
        {"id": "TX006", "region": "R-E"},
        {"id": "TX007", "region": "R-W"},
        {"id": "TX008", "region": "R-W"},
        {"id": "TX009", "region": "R-C"},
        {"id": "TX010", "region": "R-C"},
    ]
    
    # Agent configuration
    agents = [
        {"id": "monitor-agent-01", "type": "monitor"},
        {"id": "predict-agent-01", "type": "predict"},
        {"id": "decide-agent-01", "type": "decide"},
        {"id": "action-agent-01", "type": "action"},
        {"id": "learn-agent-01", "type": "learn"},
    ]
    
    print("=" * 60)
    print("🚀 TRACE Demo Simulation")
    print("=" * 60)
    print(f"Duration: {duration_seconds}s | Interval: {interval}s")
    print(f"Towers: {len(towers)} | Agents: {len(agents)}")
    print("=" * 60)
    
    start_time = time.time()
    iteration = 0
    
    while (time.time() - start_time) < duration_seconds:
        iteration += 1
        print(f"\n📊 Iteration {iteration} ({datetime.now().strftime('%H:%M:%S')})")
        
        # Generate tower telemetry with occasional anomalies
        tower_records = []
        for tower in towers:
            # 10% chance of anomaly
            healthy = random.random() > 0.10
            telemetry = generate_tower_telemetry(
                tower["id"], 
                tower["region"], 
                healthy
            )
            tower_records.append(telemetry)
            
            # Log anomalies
            if not healthy:
                print(f"  ⚠️ Anomaly detected at {tower['id']}: {telemetry['metrics']}")
        
        # Send tower telemetry
        send_to_kinesis(tower_records)
        
        # Generate agent states
        agent_records = []
        for agent in agents:
            # 5% chance of agent degradation
            healthy = random.random() > 0.05
            state = generate_agent_state(agent["id"], agent["type"], healthy)
            agent_records.append(state)
            
            if not healthy:
                print(f"  🤖 Agent {agent['id']} degraded: {state['success_rate']:.0%} success rate")
        
        # Summary
        healthy_towers = sum(1 for r in tower_records if r["status"] == "healthy")
        healthy_agents = sum(1 for r in agent_records if r["status"] == "active")
        avg_cpu = sum(r["metrics"]["cpu_percent"] for r in tower_records) / len(tower_records)
        avg_users = sum(r["metrics"]["connected_users"] for r in tower_records)
        
        print(f"  📈 Summary: {healthy_towers}/{len(towers)} towers healthy, "
              f"{healthy_agents}/{len(agents)} agents active")
        print(f"  📈 Avg CPU: {avg_cpu:.1f}%, Total Users: {avg_users}")
        
        # Wait for next interval
        time.sleep(interval)
    
    print("\n" + "=" * 60)
    print("✅ Simulation complete!")
    print("=" * 60)


def simulate_incident():
    """Simulate a network incident for self-healing demonstration."""
    
    print("=" * 60)
    print("🔥 Simulating Network Incident")
    print("=" * 60)
    
    # Create incident scenario
    incident = {
        "incident_id": f"INC-{int(time.time())}",
        "type": "high_latency",
        "tower_id": "TX003",
        "region": "R-S",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metrics": {
            "latency_ms": 250,
            "cpu_percent": 92,
            "connected_users": 950,
        },
        "severity": "high",
    }
    
    print(f"📍 Incident: {incident['incident_id']}")
    print(f"   Tower: {incident['tower_id']} ({incident['region']})")
    print(f"   Type: {incident['type']}")
    print(f"   Severity: {incident['severity']}")
    print(f"   Metrics: Latency={incident['metrics']['latency_ms']}ms, "
          f"CPU={incident['metrics']['cpu_percent']}%")
    
    # Send to Kinesis
    print("\n📤 Sending incident to data pipeline...")
    send_to_kinesis([incident])
    
    # Log to DynamoDB
    print("📝 Logging incident to database...")
    try:
        table = dynamodb.Table("trace-remediation-log")
        table.put_item(Item={
            "incident_id": incident["incident_id"],
            "tower_id": incident["tower_id"],
            "timestamp": incident["timestamp"],
            "status": "detected",
            "details": incident,
        })
        print("   ✅ Incident logged successfully")
    except Exception as e:
        print(f"   ⚠️ Logging failed: {e}")
    
    print("\n🔧 Self-healing workflow should trigger automatically...")
    print("   Check Step Functions console for execution status")
    
    return incident


def simulate_energy_optimization():
    """Simulate energy optimization opportunity."""
    
    print("=" * 60)
    print("💡 Simulating Energy Optimization Scenario")
    print("=" * 60)
    
    # Low traffic period data
    low_traffic_towers = []
    for i in range(1, 6):
        tower = {
            "tower_id": f"TX00{i}",
            "region": "R-E",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metrics": {
                "cpu_percent": random.uniform(15, 25),
                "memory_percent": random.uniform(20, 35),
                "connected_users": random.randint(50, 150),
                "trx_active": 8,  # All active but low traffic
                "trx_total": 8,
                "traffic_gbps": random.uniform(0.5, 1.5),
                "energy_kwh": random.uniform(18, 22),
            },
            "period": "off_peak",
        }
        low_traffic_towers.append(tower)
    
    print(f"🌙 Off-peak period detected")
    print(f"📍 Region: R-E")
    print(f"🏗️ Towers: {len(low_traffic_towers)}")
    
    total_users = sum(t["metrics"]["connected_users"] for t in low_traffic_towers)
    avg_traffic = sum(t["metrics"]["traffic_gbps"] for t in low_traffic_towers) / len(low_traffic_towers)
    
    print(f"\n📊 Current Status:")
    print(f"   Total Users: {total_users}")
    print(f"   Avg Traffic: {avg_traffic:.2f} Gbps")
    print(f"   TRX Active: {sum(t['metrics']['trx_active'] for t in low_traffic_towers)}")
    print(f"   Energy: {sum(t['metrics']['energy_kwh'] for t in low_traffic_towers):.1f} kWh")
    
    # Calculate optimization potential
    trx_to_shutdown = 2 * len(low_traffic_towers)  # 2 per tower
    energy_savings = trx_to_shutdown * 2.5  # ~2.5 kWh per TRX
    
    print(f"\n💡 Optimization Opportunity:")
    print(f"   TRX to shutdown: {trx_to_shutdown}")
    print(f"   Estimated savings: {energy_savings:.1f} kWh")
    print(f"   Cost savings: ~${energy_savings * 0.12:.2f}/hour")
    
    # Send data to pipeline
    print("\n📤 Sending to data pipeline...")
    send_to_kinesis(low_traffic_towers)
    
    print("\n🔧 Energy optimization workflow should analyze this data")
    print("   Check Step Functions console for optimization recommendations")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TRACE Demo Simulation")
    parser.add_argument(
        "--mode",
        choices=["continuous", "incident", "energy", "all"],
        default="all",
        help="Simulation mode"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration in seconds for continuous mode"
    )
    
    args = parser.parse_args()
    
    if args.mode == "continuous":
        run_simulation(duration_seconds=args.duration)
    elif args.mode == "incident":
        simulate_incident()
    elif args.mode == "energy":
        simulate_energy_optimization()
    elif args.mode == "all":
        print("🎬 Running full demo sequence...\n")
        
        # Brief simulation
        run_simulation(duration_seconds=15, interval=3.0)
        
        time.sleep(2)
        
        # Incident simulation
        simulate_incident()
        
        time.sleep(2)
        
        # Energy optimization
        simulate_energy_optimization()
        
        print("\n" + "=" * 60)
        print("🎉 Full demo complete!")
        print("=" * 60)


if __name__ == "__main__":
    main()
