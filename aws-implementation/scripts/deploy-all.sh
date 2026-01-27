#!/bin/bash

# TRACE AWS Implementation - Deploy All
# This script deploys all components of TRACE on AWS

set -e

echo "========================================"
echo "TRACE AWS Implementation - Full Deploy"
echo "========================================"
echo ""

# Configuration
export TRACE_ENV="${TRACE_ENV:-dev}"
export AWS_REGION="${AWS_REGION:-us-east-1}"

echo "Environment: $TRACE_ENV"
echo "Region: $AWS_REGION"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt -q
echo ""

# Deploy each component
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "Step 1: Infrastructure Setup"
echo "========================================"
cd "$SCRIPT_DIR/01-infrastructure"
python3 setup-infrastructure.py
echo ""

echo "========================================"
echo "Step 2: Data Pipeline"
echo "========================================"
cd "$SCRIPT_DIR/02-data-pipeline"
python3 setup-pipeline.py
echo ""

echo "========================================"
echo "Step 3: ML Models"
echo "========================================"
cd "$SCRIPT_DIR/03-ml-models"
python3 deploy-models.py
echo ""

echo "========================================"
echo "Step 4: Agent Tools"
echo "========================================"
cd "$SCRIPT_DIR/04-agent-tools"
python3 deploy-tools.py
echo ""

echo "========================================"
echo "Step 5: Bedrock Agents"
echo "========================================"
cd "$SCRIPT_DIR/05-bedrock-agents"
python3 deploy-agents.py
echo ""

echo "========================================"
echo "Step 6: Step Functions"
echo "========================================"
cd "$SCRIPT_DIR/06-step-functions"
python3 deploy-workflows.py
echo ""

echo "========================================"
echo "Step 7: API Gateway"
echo "========================================"
cd "$SCRIPT_DIR/07-api-gateway"
python3 deploy-api.py
echo ""

echo "========================================"
echo "Step 8: Frontend"
echo "========================================"
cd "$SCRIPT_DIR/08-frontend"
python3 deploy-frontend.py
echo ""

echo "========================================"
echo "✅ TRACE AWS Deployment Complete!"
echo "========================================"
echo ""
echo "Check the following files for deployment details:"
echo "  - infrastructure-outputs.json"
echo "  - tool-arns.json"
echo "  - agent-info.json"
echo "  - stepfunctions-outputs.json"
echo "  - api-outputs.json"
echo "  - frontend-outputs.json"
echo ""

# Print summary
cd "$SCRIPT_DIR"
if [ -f "api-outputs.json" ]; then
    echo "API URL:"
    python3 -c "import json; print('  ' + json.load(open('api-outputs.json'))['rest_api']['api_url'])"
fi

if [ -f "frontend-outputs.json" ]; then
    echo ""
    echo "Frontend URL:"
    python3 -c "import json; d=json.load(open('frontend-outputs.json')); print('  ' + (d.get('cloudfront', {}).get('url', '') or d.get('s3', {}).get('url', '')))"
fi

echo ""
echo "Run 'python3 scripts/test-agents.py' to test the deployment"
