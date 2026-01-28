# TRACE - Telecom RAN AI-Powered Cognitive Engine

Autonomous AI system for telecom network management using Amazon Bedrock multi-agent architecture.

Live Demo: https://d1cmtnu8ims6nq.cloudfront.net

## Overview

TRACE uses 8 specialized AI agents built on Amazon Bedrock to monitor, analyze, and automatically remediate telecom network issues. The system processes real-time telemetry data from cell towers, detects anomalies, and executes self-healing actions without human intervention.

## AWS Services

- Amazon Bedrock: 8 AI agents using Claude 3 Sonnet
- AWS Lambda: Serverless functions for health monitoring and remediation
- Amazon DynamoDB: Data storage for tower config, agent status, and logs
- Amazon API Gateway: REST API endpoints
- Amazon S3: Frontend hosting
- Amazon CloudFront: Content delivery
- AWS IAM: Security and access control

## AI Agent Architecture

- Principal Agent: Central orchestrator for all operations
- Regional Coordinator A: Manages Region A towers
- Regional Coordinator B: Manages Region B towers
- Decision xApp: Makes remediation decisions
- Monitoring xApp: Tracks network health metrics
- Prediction xApp: Forecasts potential issues
- Action xApp: Executes remediation actions
- Learning xApp: Improves from historical data

## Technology Stack

Backend: Python 3.12, Amazon Bedrock, AWS Lambda
Frontend: React 18, Vite, Material-UI, Recharts
Database: Amazon DynamoDB
Infrastructure: API Gateway, S3, CloudFront

## Features

- Real-time network monitoring
- Automated anomaly detection
- Self-healing remediation
- Natural language chat interface
- Performance dashboards
- Multi-agent coordination

## Quick Start

1. Install dependencies: pip install -r requirements.txt
2. Configure AWS credentials
3. Deploy infrastructure using AWS CLI
4. Start frontend: cd client && npm install && npm run dev

## Project Structure

- principal_agent/: Main orchestrator agent
- principal_agent/parent_agents/: Regional coordinators
- principal_agent/tools/: Agent tools and utilities
- client/: React frontend dashboard
- data/: Sample telemetry data

## License

MIT License
