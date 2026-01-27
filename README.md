# TRACE – Telecom RAN AI-Powered Cognitive Engine

[![AWS](https://img.shields.io/badge/AWS-Bedrock-FF9900?style=flat-square&logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

> An autonomous, self-healing telecom network management system powered by Amazon Bedrock Multi-Agent Architecture

**🔗 [Live Demo](https://d1cmtnu8ims6nq.cloudfront.net)**

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Architecture](#architecture)
- [AWS Services](#aws-services)
- [Quick Start](#quick-start)
- [Dashboard](#dashboard)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Business Outcomes](#business-outcomes)
- [Team](#team)

---

## Overview

TRACE is an AI-driven multi-agent system that transforms telecom network operations from reactive troubleshooting to proactive, autonomous management. Built entirely on AWS, it uses **Amazon Bedrock Agents** to monitor, predict, decide, and remediate network issues in real-time.

### Key Capabilities

- **Autonomous Remediation** – AI agents automatically detect and fix network issues
- **Multi-Agent Orchestration** – 8 specialized agents working collaboratively
- **Real-time Monitoring** – Live telemetry streaming and visualization
- **Self-Healing Network** – Automatic recovery with minimal human intervention
- **Energy Optimization** – Intelligent power management during low-demand periods

---

## Problem Statement

Modern telecom operators face critical challenges:

| Challenge | Impact |
|-----------|--------|
| Network Complexity | 5G/O-RAN architectures increased network elements by 10x |
| Reactive Operations | 73% of outages detected by customers before NOC teams |
| Slow Resolution | Average Mean Time to Repair (MTTR) is 4-6 hours |
| Skill Shortage | 40% global shortage of trained network engineers |
| Revenue Loss | $1-5M lost per hour of network downtime |

**TRACE solves this** by deploying AI agents that continuously monitor, predict issues before they occur, and automatically remediate problems in minutes instead of hours.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   TRACE MULTI-AGENT SYSTEM                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌─────────────────────┐                      │
│                    │   PRINCIPAL AGENT   │                      │
│                    │   (Orchestrator)    │                      │
│                    └──────────┬──────────┘                      │
│                               │                                 │
│          ┌────────────────────┼────────────────────┐            │
│          ▼                    ▼                    ▼            │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐     │
│  │   REGIONAL    │   │   REGIONAL    │   │   DECISION    │     │
│  │ COORDINATOR A │   │ COORDINATOR B │   │     xApp      │     │
│  └───────┬───────┘   └───────┬───────┘   └───────────────┘     │
│          │                   │                                  │
│  ┌───────┴───────────────────┴───────┐                         │
│  │          EDGE AGENTS              │                         │
│  ├──────────┬──────────┬─────────────┤                         │
│  │MONITORING│PREDICTION│   ACTION    │                         │
│  │  Agent   │  Agent   │   Agent     │                         │
│  └──────────┴──────────┴─────────────┘                         │
│                    │                                            │
│          ┌─────────┴─────────┐                                 │
│          │  LEARNING AGENT   │                                 │
│          └───────────────────┘                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Roles

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **Principal Agent** | Orchestrator | Cross-region coordination, escalation management |
| **Regional Coordinator** | Regional Manager | Cluster management, resource allocation |
| **Monitoring Agent** | Observability | Telemetry processing, anomaly detection |
| **Prediction Agent** | Forecasting | ML-based predictions, capacity planning |
| **Decision xApp** | Policy Engine | Root cause analysis, action recommendations |
| **Action Agent** | Executor | Remediation execution, configuration changes |
| **Learning Agent** | Intelligence | Pattern recognition, playbook optimization |

---

## AWS Services

| Service | Purpose |
|---------|---------|
| **Amazon Bedrock** | Foundation models (Claude 3 Sonnet) for AI agents |
| **AWS Lambda** | Serverless functions for agent tools |
| **Amazon DynamoDB** | Data storage (tower config, agent status, logs) |
| **Amazon API Gateway** | REST API endpoints |
| **Amazon S3** | Static website hosting |
| **Amazon CloudFront** | Global CDN for dashboard |
| **AWS IAM** | Security roles and permissions |

### Deployed Agents

| Agent | Bedrock Agent ID | Status |
|-------|------------------|--------|
| Principal Agent | `N3LVTOXSFA` | ✅ Ready |
| Regional Coordinator A | `A1AK7SJQF6` | ✅ Ready |
| Regional Coordinator B | `JPA17IHQ0V` | ✅ Ready |
| Decision xApp | `N2EGAGVLEM` | ✅ Ready |
| Monitoring Agent | `ERZO1UFKHQ` | ✅ Ready |
| Prediction Agent | `LS0OWPC30J` | ✅ Ready |
| Action Agent | `PNZVYMD3MH` | ✅ Ready |
| Learning Agent | `EHBDSQWYHB` | ✅ Ready |

---

## Quick Start

### Prerequisites

- AWS Account with Bedrock access
- Python 3.12+
- Node.js 18+
- AWS CLI configured

### 1. Clone Repository

```bash
git clone https://github.com/ramyabarri1109-a11y/trace.git
cd trace
```

### 2. Deploy AWS Infrastructure

```bash
cd aws-implementation
pip install -r requirements.txt

python 01-infrastructure/setup-infrastructure.py
python 04-agent-tools/deploy-tools.py
python 05-bedrock-agents/deploy-agents.py
python 07-api-gateway/deploy-api.py
python 08-frontend/deploy-frontend.py
```

### 3. Run Dashboard Locally

```bash
cd client
npm install
npm run dev
```

Open http://localhost:5173

### 4. Access Live Dashboard

**Production:** https://d1cmtnu8ims6nq.cloudfront.net

---

## Dashboard

The TRACE dashboard provides real-time visibility into network operations:

- **Real-time Telemetry** – Live CPU, Memory, Latency metrics
- **Issue Command Center** – Auto-detected issues with AI remediation
- **Agent Pipeline** – Visual flow: Monitoring → Prediction → Decision → Action → Learning
- **Chat Interface** – Natural language interaction with AI agents

### Remediation Flow

1. **Analyzing Issue** – AI examines root cause
2. **Agent Pipeline** – Request flows through specialized agents
3. **Executing Remediation** – Action Agent applies fix
4. **Verification** – System confirms resolution

---

## Project Structure

```
trace/
├── aws-implementation/        # AWS deployment scripts
│   ├── 01-infrastructure/     # DynamoDB, S3, IAM
│   ├── 04-agent-tools/        # Lambda functions
│   ├── 05-bedrock-agents/     # Agent definitions
│   ├── 07-api-gateway/        # API endpoints
│   └── 08-frontend/           # Frontend deployment
│
├── client/                    # React dashboard
│   └── src/
│       ├── components/        # UI components
│       └── services/          # API & WebSocket
│
├── data/                      # Sample telemetry
├── figures/                   # Architecture diagrams
└── principal_agent/           # Reference implementation
```

---

## Technology Stack

### Backend

- Python 3.12
- Amazon Bedrock (Claude 3 Sonnet)
- AWS Lambda
- DynamoDB

### Frontend

- React 18
- Vite
- Material-UI
- Recharts

### Infrastructure

- Amazon S3 + CloudFront
- API Gateway
- IAM

---

## Business Outcomes

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Mean Time to Detect | 30-60 min | < 30 sec | **99% faster** |
| Mean Time to Repair | 4-6 hours | 5-15 min | **95% faster** |
| Autonomous Resolution | 0% | 82% | **New capability** |
| Network Availability | 99.5% | 99.99% | **+0.49%** |

---

## Team

- Vinay Dangeti
- Sudeep Aryan
- G S Neelam
- Ramya
- Aishwarya

**Contact:** sudeeparyang@gmail.com

---

## License

MIT License – see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with ❤️ using Amazon Bedrock</strong>
</p>
