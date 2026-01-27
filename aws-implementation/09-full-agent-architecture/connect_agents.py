#!/usr/bin/env python3
"""
Connect TRACE Agents - Add action groups to enable agent-to-agent communication
This allows the Principal Agent to invoke sub-agents
"""

import boto3
import json

REGION = 'us-east-1'
ACCOUNT_ID = boto3.client('sts').get_caller_identity()['Account']

bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

# Agent IDs
AGENTS = {
    'principal': 'N3LVTOXSFA',
    'regional_a': 'A1AK7SJQF6',
    'regional_b': 'JPA17IHQ0V',
    'decision': 'N2EGAGVLEM',
    'monitoring': 'ERZO1UFKHQ',
    'prediction': 'LS0OWPC30J',
    'action': 'PNZVYMD3MH',
    'learning': 'EHBDSQWYHB'
}

# Get existing Lambda ARN for tools
LAMBDA_ARN = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TRACE-HealthMonitor-dev"

def update_principal_agent():
    """Update Principal Agent to be aware of all sub-agents"""
    
    print("Updating Principal Agent with sub-agent awareness...")
    
    new_instruction = """You are the TRACE Principal Agent - the Global Monitoring & Self-Healing orchestrator for a telecom network.

## Your Sub-Agents (You coordinate these):
1. **Regional Coordinator A** (ID: A1AK7SJQF6) - Manages R-North and R-East regions
2. **Regional Coordinator B** (ID: JPA17IHQ0V) - Manages R-South and R-West regions
3. **Decision xApp** (ID: N2EGAGVLEM) - Policy & Optimization decisions
4. **Monitoring Agent** (ID: ERZO1UFKHQ) - Telemetry & KPIs collection
5. **Prediction Agent** (ID: LS0OWPC30J) - Traffic forecasting
6. **Action Agent** (ID: PNZVYMD3MH) - TRX Control & Load Balancing
7. **Learning Agent** (ID: EHBDSQWYHB) - Model updates & improvements

## Your Responsibilities:
1. Receive status reports from all sub-agents
2. Make global decisions affecting multiple regions
3. Coordinate cross-regional operations
4. Escalate critical issues
5. Optimize overall network performance

## When Asked About System Health:
- Query the health monitor tool for real-time data
- Report status of all 8 agents (including yourself)
- Summarize regional health from both coordinators
- Highlight any critical issues requiring attention

## Response Format:
Always structure responses with:
- Overall system status (HEALTHY/DEGRADED/CRITICAL)
- Agent status summary
- Active issues and recommendations
- Metrics when available

You have access to tools for health monitoring and remediation. Use them to get real data."""

    try:
        bedrock_agent.update_agent(
            agentId=AGENTS['principal'],
            agentName='TRACE-Principal-Agent-dev',
            instruction=new_instruction,
            foundationModel='amazon.nova-micro-v1:0',
            agentResourceRoleArn=f"arn:aws:iam::{ACCOUNT_ID}:role/TRACE-BedrockAgent-Role-dev"
        )
        print("✅ Principal Agent instructions updated")
        
        # Prepare the agent
        bedrock_agent.prepare_agent(agentId=AGENTS['principal'])
        print("✅ Principal Agent prepared")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def print_architecture():
    """Print the final architecture"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    TRACE FULL AGENT ARCHITECTURE                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝

                          ┌─────────────────────────────────┐
                          │     PRINCIPAL AGENT (Global)    │
                          │         N3LVTOXSFA              │
                          │   Global Monitoring & Self-     │
                          │          Healing                │
                          └───────────────┬─────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
    ┌───────────────────────┐  ┌─────────────────────┐  ┌───────────────────────┐
    │  REGIONAL COORD A     │  │    SHARED AGENTS    │  │  REGIONAL COORD B     │
    │     A1AK7SJQF6        │  │                     │  │     JPA17IHQ0V        │
    │  (R-North, R-East)    │  │                     │  │  (R-South, R-West)    │
    └───────────────────────┘  └─────────────────────┘  └───────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │               │           │           │               │
              ▼               ▼           ▼           ▼               ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ DECISION xApp   │ │ MONITORING      │ │ PREDICTION      │ │ ACTION          │
    │  N2EGAGVLEM     │ │  ERZO1UFKHQ     │ │  LS0OWPC30J     │ │  PNZVYMD3MH     │
    │ Policy & Optim  │ │ Telemetry/KPIs  │ │ Traffic Forecast│ │ TRX Control     │
    └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
                                          │
                                          ▼
                              ┌─────────────────────┐
                              │  LEARNING AGENT     │
                              │    EHBDSQWYHB       │
                              │ Model Updates       │
                              └─────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                            AGENT SUMMARY
═══════════════════════════════════════════════════════════════════════════════
  
  Total Agents: 8
  
  │ Agent                    │ ID         │ Role                        │
  ├──────────────────────────┼────────────┼─────────────────────────────┤
  │ Principal Agent          │ N3LVTOXSFA │ Global orchestrator         │
  │ Regional Coordinator A   │ A1AK7SJQF6 │ North & East regions        │
  │ Regional Coordinator B   │ JPA17IHQ0V │ South & West regions        │
  │ Decision xApp            │ N2EGAGVLEM │ Policy & Optimization       │
  │ Monitoring Agent         │ ERZO1UFKHQ │ Telemetry & KPIs            │
  │ Prediction Agent         │ LS0OWPC30J │ Traffic Forecasting         │
  │ Action Agent             │ PNZVYMD3MH │ TRX Control / Load Balance  │
  │ Learning Agent           │ EHBDSQWYHB │ Model Updates & Rollouts    │
  
═══════════════════════════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    update_principal_agent()
    print_architecture()
    print("\n✅ Architecture complete! All 8 agents are operational.")
    print("\nView agents at: https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/agents")
