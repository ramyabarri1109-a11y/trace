# TRACE - Traffic & Resource Agentic Control Engine

Autonomous AI system for telecom network management using Amazon Bedrock multi-agent architecture with MCP (Model Context Protocol) for agent-to-agent communication.

Live Demo: https://d1cmtnu8ims6nq.cloudfront.net

## Overview

TRACE is an agentic multi-agent system that cuts mobile-tower energy use by 30-40% during low demand and prevents congestion during traffic surges. It coordinates agents via MCP, leveraging Amazon Bedrock for intelligent cloud-edge control.

Key capabilities:
- Energy Optimization: Reduce power during low traffic with TRX shutdown and ECO modes
- Congestion Prevention: ML-based prediction and proactive load balancing
- Self-Healing: Autonomous detection and remediation of network issues

## AWS Services

- Amazon Bedrock: 8 AI agents using Claude 3 Sonnet
- AWS Lambda: Serverless functions for health monitoring and remediation
- Amazon DynamoDB: Data storage for tower config, agent status, and logs
- Amazon API Gateway: REST API endpoints
- Amazon S3: Frontend hosting
- Amazon CloudFront: Content delivery
- AWS IAM: Security and access control

## MCP on AWS

TRACE uses Model Context Protocol (MCP) tools deployed on AWS Lambda:

### AWS Lambda Deployment

```bash
# Deploy using CloudFormation
chmod +x deploy_mcp.sh
./deploy_mcp.sh
```

This deploys:
- **Lambda Function**: `trace-mcp-tools` - All MCP tools in one function
- **API Gateway**: HTTP endpoint for MCP tool invocation
- **DynamoDB Tables**: Remediation and energy logging

### MCP Tools Available

| Tool | Description |
|------|-------------|
| `get_tower_telemetry` | Real-time tower metrics |
| `detect_tower_anomalies` | Anomaly detection |
| `get_network_health_summary` | Network overview |
| `get_power_consumption_report` | Power usage & savings |
| `set_power_mode` | Change tower power mode |
| `set_active_trx` | Control active TRX count |
| `activate_warm_spare` | Enable spare capacity |
| `get_energy_recommendations` | Optimization suggestions |
| `execute_energy_optimization` | Apply energy savings |
| `execute_remediation` | Run self-healing policy |

### Test MCP API

```bash
# Get network health
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/v1/mcp/tool \
  -H 'Content-Type: application/json' \
  -d '{"tool": "get_network_health_summary", "parameters": {}}'

# Get energy recommendations
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/v1/mcp/tool \
  -H 'Content-Type: application/json' \
  -d '{"tool": "get_energy_recommendations", "parameters": {}}'
```

### Local MCP Servers (Development)

For local development, MCP servers are also available:

```bash
cd mcp_servers
pip install -r requirements.txt
python run_mcp_servers.py
```

## AI Agent Architecture

Principal Agent: Global orchestrator for self-healing and escalation management

Parent Agents:
- Regional Coordinator A: Manages Region A clusters
- Regional Coordinator B: Manages Region B clusters

Edge Agents (xApps):
- Monitoring Agent: Streams RAN KPIs and power metrics
- Prediction Agent: Short-term load forecasting
- Decision xApp: Policy engine for safe control actions
- Action Agent: Executes TRX shutdowns and warm-spare activations
- Learning Agent: Retrains models and manages rollouts

## Technology Stack

Backend: Python 3.12, Amazon Bedrock, AWS Lambda, MCP
Frontend: React 18, Vite, Material-UI, Recharts
Database: Amazon DynamoDB
Infrastructure: API Gateway, S3, CloudFront

## Features

- Real-time network monitoring
- Automated anomaly detection
- Self-healing remediation
- Energy optimization (30-40% savings)
- Congestion prevention and load balancing
- Natural language chat interface
- Performance dashboards
- Multi-agent coordination via MCP

## Quick Start

1. Install dependencies: pip install -r requirements.txt
2. Configure AWS credentials
3. Start MCP servers: cd mcp_servers && python run_mcp_servers.py
4. Deploy infrastructure using AWS CLI
5. Start frontend: cd client && npm install && npm run dev

## Project Structure

- principal_agent/: Main orchestrator agent
- principal_agent/parent_agents/: Regional coordinators
- principal_agent/tools/: Agent tools and utilities
- mcp_servers/: MCP servers for agent context sharing
- client/: React frontend dashboard
- data/: Sample telemetry data

## Team

- Vinay Dangeti
- Sudeep Aryan
- G S Neelam
- Ramya
- Aishwarya

Contact: sudeeparyang@gmail.com

## License

MIT License
