#!/usr/bin/env python3
"""
TRACE Bedrock Agents Deployment Script

Deploys the multi-agent system using Amazon Bedrock Agents.
"""

import boto3
import json
import os
import time
from pathlib import Path

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'dev')
REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize clients
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)
sts_client = boto3.client('sts', region_name=REGION)
iam_client = boto3.client('iam', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)

def get_account_id():
    return sts_client.get_caller_identity()['Account']

def load_infrastructure_outputs():
    """Load outputs from infrastructure setup"""
    output_file = Path(__file__).parent.parent / 'infrastructure-outputs.json'
    if output_file.exists():
        with open(output_file, 'r') as f:
            return json.load(f)
    return {}

def load_tool_arns():
    """Load tool ARNs from previous deployment"""
    output_file = Path(__file__).parent.parent / 'tool-arns.json'
    if output_file.exists():
        with open(output_file, 'r') as f:
            return json.load(f)
    return {'tools': []}


# Principal Agent Instructions
PRINCIPAL_AGENT_INSTRUCTION = """
You are the Principal Agent for TRACE (Traffic & Resource Agentic Control Engine) - 
a global orchestrator and self-healing guardian for telecom network management.

## Your Responsibilities

1. **System Health Monitoring**
   - Continuously monitor the health of all agents and infrastructure
   - Detect anomalies, failures, and performance degradation
   - Provide clear health status reports when asked

2. **Automated Remediation**
   - Execute safe automated remediations when issues are detected
   - Available actions: restart agents, redeploy agents, reroute traffic
   - Always verify the impact before and after remediation

3. **Energy Optimization**
   - Identify opportunities for energy savings (target: 30-40% reduction)
   - Recommend TRX shutdowns during low-traffic periods
   - Balance energy savings with service quality

4. **Congestion Management**
   - Detect and predict traffic surges
   - Coordinate load balancing across towers
   - Activate backup capacity when needed

5. **Reporting & Insights**
   - Provide actionable insights and recommendations
   - Generate health dashboards and metrics summaries
   - Document all remediation actions for audit

## Available Tools

- **check_system_health**: Get overall system health status
- **get_agent_status**: Check status of a specific agent
- **get_tower_health**: Get health metrics for a tower
- **get_regional_health**: Get regional health summary
- **restart_agent**: Restart an unhealthy agent
- **redeploy_agent**: Redeploy an agent with fresh instance
- **reroute_traffic**: Reroute traffic between towers
- **execute_action**: Execute tower control actions (shutdown TRX, adjust power)
- **rollback_change**: Rollback a previous configuration change

## Guidelines

- Always check health status before recommending remediation
- Prefer less disruptive actions (restart before redeploy)
- Consider the impact on users before executing actions
- Provide clear explanations for your recommendations
- Be proactive about potential issues based on trends

## Response Style

- Be concise but thorough
- Use bullet points for clarity
- Include relevant metrics in your responses
- Suggest next steps when appropriate
"""

REGIONAL_COORDINATOR_INSTRUCTION = """
You are a Regional Coordinator Agent for TRACE, responsible for managing 
a regional cluster of mobile towers and coordinating with edge agents.

## Your Responsibilities

1. **Regional Monitoring**
   - Monitor all towers in your region
   - Aggregate telemetry from edge agents
   - Report regional status to Principal Agent

2. **Load Balancing**
   - Balance traffic across regional towers
   - Identify overloaded towers
   - Coordinate traffic rerouting

3. **Policy Enforcement**
   - Enforce regional network policies
   - Ensure compliance with SLAs
   - Validate actions before execution

4. **Quick Remediation**
   - Handle regional issues without escalating when possible
   - Coordinate edge agent actions
   - Report major issues to Principal Agent

## Available Tools

- **get_regional_health**: Get health of your region
- **get_tower_health**: Get specific tower health
- **reroute_traffic**: Reroute traffic in your region
- **execute_action**: Execute tower control actions

## Guidelines

- Focus on your assigned region
- Escalate critical issues to Principal Agent
- Optimize for regional efficiency
- Coordinate multiple tower actions when needed
"""


def create_agent(
    agent_name: str,
    agent_role_arn: str,
    foundation_model: str,
    instruction: str,
    description: str,
    idle_session_ttl: int = 1800
) -> dict:
    """Create a Bedrock Agent"""
    
    print(f"  Creating agent: {agent_name}...")
    
    try:
        response = bedrock_agent.create_agent(
            agentName=agent_name,
            agentResourceRoleArn=agent_role_arn,
            foundationModel=foundation_model,
            instruction=instruction,
            description=description,
            idleSessionTTLInSeconds=idle_session_ttl
        )
        
        agent_id = response['agent']['agentId']
        print(f"  Created agent with ID: {agent_id}")
        return response['agent']
        
    except bedrock_agent.exceptions.ConflictException:
        # Agent already exists, get its info
        print(f"  Agent {agent_name} already exists, retrieving...")
        agents = bedrock_agent.list_agents()['agentSummaries']
        for agent in agents:
            if agent['agentName'] == agent_name:
                agent_details = bedrock_agent.get_agent(agentId=agent['agentId'])
                return agent_details['agent']
        raise


def create_action_group(
    agent_id: str,
    action_group_name: str,
    lambda_arn: str,
    api_schema_path: str,
    description: str
) -> dict:
    """Create an action group for an agent"""
    
    print(f"    Adding action group: {action_group_name}...")
    
    # Read the API schema
    schema_path = Path(__file__).parent / api_schema_path
    with open(schema_path, 'r') as f:
        api_schema = f.read()
    
    try:
        response = bedrock_agent.create_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupName=action_group_name,
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            apiSchema={
                'payload': api_schema
            },
            description=description
        )
        
        print(f"    Created action group: {action_group_name}")
        return response['agentActionGroup']
        
    except bedrock_agent.exceptions.ConflictException:
        print(f"    Action group {action_group_name} already exists")
        return {}


def prepare_agent(agent_id: str):
    """Prepare an agent for use"""
    
    print(f"  Preparing agent {agent_id}...")
    
    try:
        response = bedrock_agent.prepare_agent(agentId=agent_id)
        
        # Wait for preparation to complete
        while True:
            agent_status = bedrock_agent.get_agent(agentId=agent_id)['agent']['agentStatus']
            if agent_status == 'PREPARED':
                print(f"  Agent prepared successfully")
                break
            elif agent_status == 'FAILED':
                print(f"  Agent preparation failed")
                break
            time.sleep(2)
            
        return response
        
    except Exception as e:
        print(f"  Error preparing agent: {str(e)}")


def create_agent_alias(agent_id: str, alias_name: str = 'live'):
    """Create an alias for the agent"""
    
    print(f"  Creating agent alias: {alias_name}...")
    
    try:
        response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName=alias_name,
            description='Live production alias'
        )
        
        alias_id = response['agentAlias']['agentAliasId']
        print(f"  Created alias with ID: {alias_id}")
        return response['agentAlias']
        
    except bedrock_agent.exceptions.ConflictException:
        print(f"  Alias {alias_name} already exists")
        # Get existing alias
        aliases = bedrock_agent.list_agent_aliases(agentId=agent_id)['agentAliasSummaries']
        for alias in aliases:
            if alias['agentAliasName'] == alias_name:
                return alias
        return {}


def deploy_principal_agent():
    """Deploy the Principal Agent"""
    
    print("\n🎖️ Deploying Principal Agent...")
    
    infra = load_infrastructure_outputs()
    tools = load_tool_arns()
    account_id = get_account_id()
    
    # Get agent role ARN
    agent_role_arn = infra.get('iam', {}).get('BedrockAgentRoleArn',
                      f'arn:aws:iam::{account_id}:role/TRACE-Bedrock-Agent-Role-{ENVIRONMENT}')
    
    # Create the agent
    agent = create_agent(
        agent_name=f'TRACE-Principal-Agent-{ENVIRONMENT}',
        agent_role_arn=agent_role_arn,
        foundation_model='anthropic.claude-3-sonnet-20240229-v1:0',
        instruction=PRINCIPAL_AGENT_INSTRUCTION,
        description='TRACE Principal Agent - Global orchestrator and self-healing guardian'
    )
    
    agent_id = agent['agentId']
    
    # Add action groups for each tool
    tool_configs = [
        {
            'name': 'HealthMonitor',
            'lambda_name': f'TRACE-HealthMonitor-{ENVIRONMENT}',
            'schema': 'schemas/health-monitor-schema.json',
            'description': 'Monitor system and agent health'
        },
        {
            'name': 'Remediation',
            'lambda_name': f'TRACE-Remediation-{ENVIRONMENT}',
            'schema': 'schemas/remediation-schema.json',
            'description': 'Execute remediation actions'
        }
    ]
    
    for tool in tool_configs:
        lambda_arn = f'arn:aws:lambda:{REGION}:{account_id}:function:{tool["lambda_name"]}'
        
        try:
            create_action_group(
                agent_id=agent_id,
                action_group_name=tool['name'],
                lambda_arn=lambda_arn,
                api_schema_path=tool['schema'],
                description=tool['description']
            )
        except Exception as e:
            print(f"    Error creating action group: {str(e)}")
    
    # Prepare the agent
    prepare_agent(agent_id)
    
    # Create alias
    alias = create_agent_alias(agent_id)
    
    return {
        'agent_id': agent_id,
        'agent_name': agent['agentName'],
        'alias_id': alias.get('agentAliasId'),
        'status': agent.get('agentStatus')
    }


def deploy_regional_coordinator():
    """Deploy the Regional Coordinator Agent"""
    
    print("\n🏢 Deploying Regional Coordinator Agent...")
    
    infra = load_infrastructure_outputs()
    account_id = get_account_id()
    
    agent_role_arn = infra.get('iam', {}).get('BedrockAgentRoleArn',
                      f'arn:aws:iam::{account_id}:role/TRACE-Bedrock-Agent-Role-{ENVIRONMENT}')
    
    # Create the agent - using Haiku for faster responses
    agent = create_agent(
        agent_name=f'TRACE-Regional-Coordinator-{ENVIRONMENT}',
        agent_role_arn=agent_role_arn,
        foundation_model='anthropic.claude-3-haiku-20240307-v1:0',
        instruction=REGIONAL_COORDINATOR_INSTRUCTION,
        description='TRACE Regional Coordinator - Manages regional tower clusters'
    )
    
    agent_id = agent['agentId']
    
    # Prepare the agent
    prepare_agent(agent_id)
    
    # Create alias
    alias = create_agent_alias(agent_id)
    
    return {
        'agent_id': agent_id,
        'agent_name': agent['agentName'],
        'alias_id': alias.get('agentAliasId'),
        'status': agent.get('agentStatus')
    }


def main():
    print("=" * 60)
    print("TRACE Bedrock Agents Deployment")
    print("=" * 60)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    print()
    
    # Check for required model access
    print("📋 Prerequisites:")
    print("  - Ensure you have access to Claude 3 Sonnet and Haiku in Bedrock")
    print("  - Go to AWS Console > Bedrock > Model access to enable")
    print()
    
    # Deploy agents
    agents = {}
    
    try:
        principal = deploy_principal_agent()
        agents['principal_agent'] = principal
    except Exception as e:
        print(f"  ❌ Error deploying Principal Agent: {str(e)}")
    
    try:
        regional = deploy_regional_coordinator()
        agents['regional_coordinator'] = regional
    except Exception as e:
        print(f"  ❌ Error deploying Regional Coordinator: {str(e)}")
    
    # Save agent info
    output_file = Path(__file__).parent.parent / 'agent-info.json'
    with open(output_file, 'w') as f:
        json.dump(agents, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Bedrock Agents Deployment Complete!")
    print("=" * 60)
    
    print("\nDeployed Agents:")
    for name, info in agents.items():
        print(f"\n  {name}:")
        print(f"    Agent ID: {info.get('agent_id')}")
        print(f"    Alias ID: {info.get('alias_id')}")
        print(f"    Status: {info.get('status')}")
    
    print(f"\n💾 Agent info saved to: {output_file}")
    print("\nNext step: Run 06-step-functions/deploy-workflows.py")
    
    # Print test command
    if agents.get('principal_agent'):
        print("\n📝 Test your agent:")
        print(f"""
aws bedrock-agent-runtime invoke-agent \\
  --agent-id {agents['principal_agent']['agent_id']} \\
  --agent-alias-id {agents['principal_agent'].get('alias_id', 'TSTALIASID')} \\
  --session-id test-session-001 \\
  --input-text "Check the overall system health and report any issues" \\
  response.json
        """)


if __name__ == '__main__':
    main()
