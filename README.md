<p align="center"># TRACE – Telecom RAN AI-Powered Cognitive Engine

  <img src="figures/07_dashboard.png" alt="TRACE Dashboard" width="800"/>

</p>[![AWS](https://img.shields.io/badge/AWS-Bedrock-FF9900?style=flat-square&logo=amazon-aws)](https://aws.amazon.com/bedrock/)

[![React](https://img.shields.io/badge/React-18.2-61DAFB?style=flat-square&logo=react)](https://react.dev/)

<h1 align="center">TRACE</h1>[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python)](https://python.org/)

<h3 align="center">Telecom RAN AI-Powered Cognitive Engine</h3>[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)



<p align="center">> An autonomous, self-healing telecom network management system powered by Amazon Bedrock Multi-Agent Architecture

  <a href="https://aws.amazon.com/bedrock/"><img src="https://img.shields.io/badge/Amazon-Bedrock-FF9900?style=for-the-badge&logo=amazon-aws" alt="AWS Bedrock"/></a>

  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react" alt="React"/></a>**🔗 [Live Demo](https://d1cmtnu8ims6nq.cloudfront.net)**

  <a href="https://python.org/"><img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>

  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>---

</p>

## Table of Contents

<p align="center">

  An autonomous, self-healing telecom network management system<br/>- [Overview](#overview)

  powered by Amazon Bedrock Multi-Agent Architecture- [Problem Statement](#problem-statement)

</p>- [Architecture](#architecture)

- [AWS Services](#aws-services)

<p align="center">- [Quick Start](#quick-start)

  <a href="https://d1cmtnu8ims6nq.cloudfront.net"><strong>🔗 Live Demo</strong></a> ·- [Dashboard](#dashboard)

  <a href="#quick-start"><strong>Quick Start</strong></a> ·- [Project Structure](#project-structure)

  <a href="#architecture"><strong>Architecture</strong></a>- [Technology Stack](#technology-stack)

</p>- [Business Outcomes](#business-outcomes)

- [Team](#team)

---

---

## About

## Overview

TRACE transforms telecom network operations from reactive troubleshooting to **proactive, autonomous management**. Using 8 specialized AI agents powered by Amazon Bedrock, it monitors network health, predicts issues before they occur, and automatically remediates problems—reducing resolution time from hours to minutes.

TRACE is an AI-driven multi-agent system that transforms telecom network operations from reactive troubleshooting to proactive, autonomous management. Built entirely on AWS, it uses **Amazon Bedrock Agents** to monitor, predict, decide, and remediate network issues in real-time.

### ✨ Key Features

### Key Capabilities

- **🤖 Autonomous Remediation** – AI agents automatically detect and fix network issues

- **🔄 Multi-Agent Orchestration** – 8 specialized agents working collaboratively  - **Autonomous Remediation** – AI agents automatically detect and fix network issues

- **📊 Real-time Monitoring** – Live telemetry streaming and visualization- **Multi-Agent Orchestration** – 8 specialized agents working collaboratively

- **🔧 Self-Healing Network** – Automatic recovery with minimal human intervention- **Real-time Monitoring** – Live telemetry streaming and visualization

- **⚡ Energy Optimization** – Intelligent power management during low-demand periods- **Self-Healing Network** – Automatic recovery with minimal human intervention

- **Energy Optimization** – Intelligent power management during low-demand periods

---

---

## Problem

## Problem Statement

| Challenge | Impact |

|-----------|--------|Modern telecom operators face critical challenges:

| Network Complexity | 5G/O-RAN increased network elements by **10x** |

| Reactive Operations | **73%** of outages detected by customers first || Challenge | Impact |

| Slow Resolution | Average MTTR is **4-6 hours** ||-----------|--------|

| Skill Shortage | **40%** global shortage of network engineers || Network Complexity | 5G/O-RAN architectures increased network elements by 10x |

| Revenue Loss | **$1-5M** lost per hour of downtime || Reactive Operations | 73% of outages detected by customers before NOC teams |

| Slow Resolution | Average Mean Time to Repair (MTTR) is 4-6 hours |

---| Skill Shortage | 40% global shortage of trained network engineers |

| Revenue Loss | $1-5M lost per hour of network downtime |

## Architecture

**TRACE solves this** by deploying AI agents that continuously monitor, predict issues before they occur, and automatically remediate problems in minutes instead of hours.

<p align="center">

  <img src="figures/01_architecture.png" alt="TRACE Architecture" width="700"/>---

</p>

## Architecture

### Agent Hierarchy

```

```┌─────────────────────────────────────────────────────────────────┐

                    ┌─────────────────────┐│                   TRACE MULTI-AGENT SYSTEM                      │

                    │   PRINCIPAL AGENT   │├─────────────────────────────────────────────────────────────────┤

                    │   (Orchestrator)    ││                                                                 │

                    └──────────┬──────────┘│                    ┌─────────────────────┐                      │

                               ││                    │   PRINCIPAL AGENT   │                      │

          ┌────────────────────┼────────────────────┐│                    │   (Orchestrator)    │                      │

          ▼                    ▼                    ▼│                    └──────────┬──────────┘                      │

  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐│                               │                                 │

  │   REGIONAL    │   │   REGIONAL    │   │   DECISION    ││          ┌────────────────────┼────────────────────┐            │

  │ COORDINATOR A │   │ COORDINATOR B │   │     xApp      ││          ▼                    ▼                    ▼            │

  └───────────────┘   └───────────────┘   └───────────────┘│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐     │

          │                   ││  │   REGIONAL    │   │   REGIONAL    │   │   DECISION    │     │

          └─────────┬─────────┘│  │ COORDINATOR A │   │ COORDINATOR B │   │     xApp      │     │

                    ▼│  └───────┬───────┘   └───────┬───────┘   └───────────────┘     │

  ┌──────────────────────────────────────────────────────┐│          │                   │                                  │

  │  MONITORING  │  PREDICTION  │  ACTION  │  LEARNING   ││  ┌───────┴───────────────────┴───────┐                         │

  │    Agent     │    Agent     │  Agent   │   Agent     ││  │          EDGE AGENTS              │                         │

  └──────────────────────────────────────────────────────┘│  ├──────────┬──────────┬─────────────┤                         │

```│  │MONITORING│PREDICTION│   ACTION    │                         │

│  │  Agent   │  Agent   │   Agent     │                         │

| Agent | Role |│  └──────────┴──────────┴─────────────┘                         │

|-------|------|│                    │                                            │

| **Principal** | Global orchestration, escalation management |│          ┌─────────┴─────────┐                                 │

| **Regional Coordinators** | Cluster management, resource allocation |│          │  LEARNING AGENT   │                                 │

| **Monitoring** | Telemetry processing, anomaly detection |│          └───────────────────┘                                 │

| **Prediction** | ML-based forecasting, capacity planning |│                                                                 │

| **Decision xApp** | Root cause analysis, action recommendations |└─────────────────────────────────────────────────────────────────┘

| **Action** | Remediation execution, configuration changes |```

| **Learning** | Pattern recognition, playbook optimization |

### Agent Roles

---

| Agent | Role | Responsibilities |

## Built With|-------|------|------------------|

| **Principal Agent** | Orchestrator | Cross-region coordination, escalation management |

| Category | Technologies || **Regional Coordinator** | Regional Manager | Cluster management, resource allocation |

|----------|--------------|| **Monitoring Agent** | Observability | Telemetry processing, anomaly detection |

| **AI/ML** | Amazon Bedrock, Claude 3 Sonnet || **Prediction Agent** | Forecasting | ML-based predictions, capacity planning |

| **Backend** | Python 3.12, AWS Lambda, DynamoDB || **Decision xApp** | Policy Engine | Root cause analysis, action recommendations |

| **Frontend** | React 18, Vite, Material-UI, Recharts || **Action Agent** | Executor | Remediation execution, configuration changes |

| **Infrastructure** | API Gateway, S3, CloudFront, IAM || **Learning Agent** | Intelligence | Pattern recognition, playbook optimization |



------



## Quick Start## AWS Services



### Prerequisites| Service | Purpose |

|---------|---------|

```| **Amazon Bedrock** | Foundation models (Claude 3 Sonnet) for AI agents |

✓ AWS Account with Bedrock access| **AWS Lambda** | Serverless functions for agent tools |

✓ Python 3.12+| **Amazon DynamoDB** | Data storage (tower config, agent status, logs) |

✓ Node.js 18+| **Amazon API Gateway** | REST API endpoints |

✓ AWS CLI configured| **Amazon S3** | Static website hosting |

```| **Amazon CloudFront** | Global CDN for dashboard |

| **AWS IAM** | Security roles and permissions |

### Installation

### Deployed Agents

```bash

# Clone the repository| Agent | Bedrock Agent ID | Status |

git clone https://github.com/ramyabarri1109-a11y/trace.git|-------|------------------|--------|

cd trace| Principal Agent | `N3LVTOXSFA` | ✅ Ready |

| Regional Coordinator A | `A1AK7SJQF6` | ✅ Ready |

# Deploy AWS infrastructure| Regional Coordinator B | `JPA17IHQ0V` | ✅ Ready |

cd aws-implementation| Decision xApp | `N2EGAGVLEM` | ✅ Ready |

pip install -r requirements.txt| Monitoring Agent | `ERZO1UFKHQ` | ✅ Ready |

python 01-infrastructure/setup-infrastructure.py| Prediction Agent | `LS0OWPC30J` | ✅ Ready |

python 04-agent-tools/deploy-tools.py| Action Agent | `PNZVYMD3MH` | ✅ Ready |

python 05-bedrock-agents/deploy-agents.py| Learning Agent | `EHBDSQWYHB` | ✅ Ready |

python 07-api-gateway/deploy-api.py

python 08-frontend/deploy-frontend.py---



# Run dashboard locally## Quick Start

cd ../client

npm install### Prerequisites

npm run dev

```- AWS Account with Bedrock access

- Python 3.12+

Open [http://localhost:5173](http://localhost:5173)- Node.js 18+

- AWS CLI configured

### Live Demo

### 1. Clone Repository

**Production Dashboard:** [https://d1cmtnu8ims6nq.cloudfront.net](https://d1cmtnu8ims6nq.cloudfront.net)

```bash

---git clone https://github.com/ramyabarri1109-a11y/trace.git

cd trace

## Dashboard```



<p align="center">### 2. Deploy AWS Infrastructure

  <img src="figures/07_dashboard.png" alt="Dashboard Features" width="700"/>

</p>```bash

cd aws-implementation

| Feature | Description |pip install -r requirements.txt

|---------|-------------|

| **Real-time Telemetry** | Live CPU, Memory, Latency metrics |python 01-infrastructure/setup-infrastructure.py

| **Issue Command Center** | Auto-detected issues with severity indicators |python 04-agent-tools/deploy-tools.py

| **Agent Pipeline** | Visual flow: Monitoring → Prediction → Decision → Action |python 05-bedrock-agents/deploy-agents.py

| **Chat Interface** | Natural language interaction with AI agents |python 07-api-gateway/deploy-api.py

| **One-Click Remediation** | Execute AI-powered fixes instantly |python 08-frontend/deploy-frontend.py

```

---

### 3. Run Dashboard Locally

## Results

```bash

| Metric | Before | After | Improvement |cd client

|--------|--------|-------|:-----------:|npm install

| Mean Time to Detect | 30-60 min | < 30 sec | **99%** ⬇️ |npm run dev

| Mean Time to Repair | 4-6 hours | 5-15 min | **95%** ⬇️ |```

| Autonomous Resolution | 0% | 82% | **New** ✨ |

| Network Availability | 99.5% | 99.99% | **+0.49%** ⬆️ |Open http://localhost:5173



---### 4. Access Live Dashboard



## Project Structure**Production:** https://d1cmtnu8ims6nq.cloudfront.net



```---

trace/

├── aws-implementation/     # AWS deployment scripts## Dashboard

│   ├── 01-infrastructure/  # DynamoDB, S3, IAM

│   ├── 04-agent-tools/     # Lambda functionsThe TRACE dashboard provides real-time visibility into network operations:

│   ├── 05-bedrock-agents/  # Agent definitions

│   ├── 07-api-gateway/     # API endpoints- **Real-time Telemetry** – Live CPU, Memory, Latency metrics

│   └── 08-frontend/        # Frontend deployment- **Issue Command Center** – Auto-detected issues with AI remediation

│- **Agent Pipeline** – Visual flow: Monitoring → Prediction → Decision → Action → Learning

├── client/                 # React dashboard- **Chat Interface** – Natural language interaction with AI agents

│   └── src/

│       ├── components/     # UI components### Remediation Flow

│       └── services/       # API & WebSocket

│1. **Analyzing Issue** – AI examines root cause

├── data/                   # Sample telemetry2. **Agent Pipeline** – Request flows through specialized agents

├── figures/                # Architecture diagrams3. **Executing Remediation** – Action Agent applies fix

└── principal_agent/        # Reference implementation4. **Verification** – System confirms resolution

```

---

---

## Project Structure

## Deployed Agents

```

| Agent | Bedrock ID | Status |trace/

|-------|------------|:------:|├── aws-implementation/        # AWS deployment scripts

| Principal Agent | `N3LVTOXSFA` | ✅ |│   ├── 01-infrastructure/     # DynamoDB, S3, IAM

| Regional Coordinator A | `A1AK7SJQF6` | ✅ |│   ├── 04-agent-tools/        # Lambda functions

| Regional Coordinator B | `JPA17IHQ0V` | ✅ |│   ├── 05-bedrock-agents/     # Agent definitions

| Decision xApp | `N2EGAGVLEM` | ✅ |│   ├── 07-api-gateway/        # API endpoints

| Monitoring Agent | `ERZO1UFKHQ` | ✅ |│   └── 08-frontend/           # Frontend deployment

| Prediction Agent | `LS0OWPC30J` | ✅ |│

| Action Agent | `PNZVYMD3MH` | ✅ |├── client/                    # React dashboard

| Learning Agent | `EHBDSQWYHB` | ✅ |│   └── src/

│       ├── components/        # UI components

---│       └── services/          # API & WebSocket

│

## Team├── data/                      # Sample telemetry

├── figures/                   # Architecture diagrams

| Member | Contact |└── principal_agent/           # Reference implementation

|--------|---------|```

| Vinay Dangeti | |

| Sudeep Aryan | sudeeparyang@gmail.com |---

| G S Neelam | |

| Ramya | |## Technology Stack

| Aishwarya | |

### Backend

---

- Python 3.12

## License- Amazon Bedrock (Claude 3 Sonnet)

- AWS Lambda

Distributed under the MIT License. See `LICENSE` for more information.- DynamoDB



---### Frontend



<p align="center">- React 18

  <sub>Built with ❤️ using Amazon Bedrock</sub>- Vite

</p>- Material-UI

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
