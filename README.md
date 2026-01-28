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

## MCP Servers

TRACE uses Model Context Protocol (MCP) for agent-to-agent context sharing:

- Telemetry Server: Real-time tower metrics and anomaly detection
- Tower Config Server: Tower configuration and management
- Energy Server: Energy optimization and power management
- Policy Server: Remediation policies and self-healing workflows

Start MCP servers:
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
