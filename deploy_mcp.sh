#!/bin/bash
# Deploy TRACE MCP Stack to AWS

echo "🚀 TRACE MCP Deployment Script"
echo "================================"

# Configuration
STACK_NAME="trace-mcp-stack"
REGION="us-east-1"
TEMPLATE_FILE="cloudformation/trace-mcp-stack.json"
LAMBDA_DIR="lambda"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
aws sts get-caller-identity > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ Using AWS Account: $ACCOUNT_ID"

# Deploy CloudFormation stack
echo ""
echo "📦 Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file $TEMPLATE_FILE \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION \
    --parameter-overrides Environment=production

if [ $? -ne 0 ]; then
    echo "❌ CloudFormation deployment failed"
    exit 1
fi

echo "✅ CloudFormation stack deployed"

# Get stack outputs
echo ""
echo "📋 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs' \
    --output table

# Package and deploy Lambda code
echo ""
echo "📦 Packaging Lambda function..."
cd $LAMBDA_DIR
zip -r mcp_tools.zip mcp_tools_lambda.py
cd ..

LAMBDA_ARN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query "Stacks[0].Outputs[?OutputKey=='MCPLambdaArn'].OutputValue" \
    --output text)

echo "🔄 Updating Lambda code..."
aws lambda update-function-code \
    --function-name trace-mcp-tools \
    --zip-file fileb://$LAMBDA_DIR/mcp_tools.zip \
    --region $REGION > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Lambda code updated"
else
    echo "⚠️  Lambda code update failed (this is normal on first deploy)"
fi

# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query "Stacks[0].Outputs[?OutputKey=='MCPApiEndpoint'].OutputValue" \
    --output text)

echo ""
echo "🎉 Deployment Complete!"
echo "========================"
echo "MCP API Endpoint: $API_ENDPOINT"
echo ""
echo "Test with:"
echo "curl -X POST $API_ENDPOINT -H 'Content-Type: application/json' -d '{\"tool\": \"get_network_health_summary\", \"parameters\": {}}'"
