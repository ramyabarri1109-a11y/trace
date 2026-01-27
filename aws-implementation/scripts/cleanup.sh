#!/bin/bash

# TRACE AWS Implementation - Cleanup
# This script removes all deployed AWS resources

set -e

echo "========================================"
echo "TRACE AWS Implementation - Cleanup"
echo "========================================"
echo ""

export TRACE_ENV="${TRACE_ENV:-dev}"
export AWS_REGION="${AWS_REGION:-us-east-1}"

echo "Environment: $TRACE_ENV"
echo "Region: $AWS_REGION"
echo ""
echo "⚠️  This will DELETE all TRACE resources in this environment!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."

# Delete CloudFormation stacks
echo ""
echo "Deleting CloudFormation stacks..."

stacks=(
    "trace-kinesis-$TRACE_ENV"
    "trace-s3-$TRACE_ENV"
    "trace-dynamodb-$TRACE_ENV"
    "trace-iam-roles-$TRACE_ENV"
)

for stack in "${stacks[@]}"; do
    echo "  Deleting stack: $stack"
    aws cloudformation delete-stack --stack-name "$stack" 2>/dev/null || echo "    (not found)"
done

# Delete Lambda functions
echo ""
echo "Deleting Lambda functions..."

functions=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'TRACE-')].FunctionName" --output text 2>/dev/null || echo "")

for func in $functions; do
    if [[ "$func" == *"$TRACE_ENV"* ]]; then
        echo "  Deleting: $func"
        aws lambda delete-function --function-name "$func" 2>/dev/null || true
    fi
done

# Delete Bedrock Agents
echo ""
echo "Deleting Bedrock Agents..."

agents=$(aws bedrock-agent list-agents --query "agentSummaries[?starts_with(agentName, 'TRACE-')].agentId" --output text 2>/dev/null || echo "")

for agent_id in $agents; do
    echo "  Deleting agent: $agent_id"
    aws bedrock-agent delete-agent --agent-id "$agent_id" 2>/dev/null || true
done

# Delete Step Functions
echo ""
echo "Deleting Step Functions..."

state_machines=$(aws stepfunctions list-state-machines --query "stateMachines[?starts_with(name, 'TRACE-')].stateMachineArn" --output text 2>/dev/null || echo "")

for sm_arn in $state_machines; do
    echo "  Deleting: $sm_arn"
    aws stepfunctions delete-state-machine --state-machine-arn "$sm_arn" 2>/dev/null || true
done

# Delete API Gateway
echo ""
echo "Deleting API Gateway..."

apis=$(aws apigateway get-rest-apis --query "items[?starts_with(name, 'TRACE-')].id" --output text 2>/dev/null || echo "")

for api_id in $apis; do
    echo "  Deleting API: $api_id"
    aws apigateway delete-rest-api --rest-api-id "$api_id" 2>/dev/null || true
done

# Delete Timestream database
echo ""
echo "Deleting Timestream database..."

aws timestream-write delete-table \
    --database-name "TRACE-Telemetry-$TRACE_ENV" \
    --table-name "TowerMetrics" 2>/dev/null || true

aws timestream-write delete-database \
    --database-name "TRACE-Telemetry-$TRACE_ENV" 2>/dev/null || true

# Empty and delete S3 buckets
echo ""
echo "Deleting S3 buckets..."

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

buckets=(
    "trace-telemetry-$ACCOUNT_ID-$TRACE_ENV"
    "trace-knowledge-base-$ACCOUNT_ID-$TRACE_ENV"
    "trace-models-$ACCOUNT_ID-$TRACE_ENV"
    "trace-lambda-code-$ACCOUNT_ID-$TRACE_ENV"
    "trace-frontend-$ACCOUNT_ID-$TRACE_ENV"
)

for bucket in "${buckets[@]}"; do
    echo "  Emptying and deleting: $bucket"
    aws s3 rm "s3://$bucket" --recursive 2>/dev/null || true
    aws s3 rb "s3://$bucket" 2>/dev/null || true
done

# Clean up local output files
echo ""
echo "Cleaning up local files..."

rm -f infrastructure-outputs.json 2>/dev/null || true
rm -f tool-arns.json 2>/dev/null || true
rm -f agent-info.json 2>/dev/null || true
rm -f stepfunctions-outputs.json 2>/dev/null || true
rm -f api-outputs.json 2>/dev/null || true
rm -f frontend-outputs.json 2>/dev/null || true

echo ""
echo "========================================"
echo "✅ Cleanup Complete!"
echo "========================================"
echo ""
echo "Note: Some resources may take a few minutes to fully delete."
echo "Check the AWS Console to verify all resources are removed."
