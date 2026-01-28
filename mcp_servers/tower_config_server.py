"""
TRACE Tower Configuration MCP Server

Exposes tower configuration, status, and management capabilities via MCP.
Enables agents to discover tower details and request configuration changes.
"""

import json
import logging
from datetime import datetime
from typing import Any
import boto3
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tower-config-mcp-server")

# Initialize MCP Server
server = Server("trace-tower-config-server")

# Sample tower configuration data
TOWER_CONFIGS = {
    "tower-001": {
        "tower_id": "tower-001",
        "name": "Downtown Tower A",
        "region": "region-a",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "capacity": 500,
        "trx_count": 4,
        "active_trx": 4,
        "antenna_count": 12,
        "frequency_bands": ["700MHz", "1900MHz", "2100MHz"],
        "status": "active",
        "power_mode": "normal",
        "last_maintenance": "2026-01-15T10:00:00Z",
        "firmware_version": "3.2.1"
    },
    "tower-002": {
        "tower_id": "tower-002",
        "name": "Uptown Tower B",
        "region": "region-a",
        "location": {"lat": 40.7831, "lon": -73.9712},
        "capacity": 400,
        "trx_count": 3,
        "active_trx": 3,
        "antenna_count": 9,
        "frequency_bands": ["700MHz", "1900MHz"],
        "status": "active",
        "power_mode": "normal",
        "last_maintenance": "2026-01-10T14:00:00Z",
        "firmware_version": "3.2.1"
    },
    "tower-003": {
        "tower_id": "tower-003",
        "name": "Harbor Tower C",
        "region": "region-b",
        "location": {"lat": 40.6892, "lon": -74.0445},
        "capacity": 600,
        "trx_count": 5,
        "active_trx": 4,
        "antenna_count": 15,
        "frequency_bands": ["700MHz", "1900MHz", "2100MHz", "2600MHz"],
        "status": "active",
        "power_mode": "eco",
        "last_maintenance": "2026-01-20T08:00:00Z",
        "firmware_version": "3.2.0"
    },
    "tower-004": {
        "tower_id": "tower-004",
        "name": "Industrial Tower D",
        "region": "region-b",
        "location": {"lat": 40.7282, "lon": -73.7949},
        "capacity": 350,
        "trx_count": 3,
        "active_trx": 2,
        "antenna_count": 9,
        "frequency_bands": ["700MHz", "1900MHz"],
        "status": "degraded",
        "power_mode": "eco",
        "last_maintenance": "2026-01-05T16:00:00Z",
        "firmware_version": "3.1.5"
    },
    "tower-005": {
        "tower_id": "tower-005",
        "name": "Suburban Tower E",
        "region": "region-a",
        "location": {"lat": 40.7589, "lon": -73.9851},
        "capacity": 450,
        "trx_count": 4,
        "active_trx": 3,
        "antenna_count": 12,
        "frequency_bands": ["700MHz", "1900MHz", "2100MHz"],
        "status": "active",
        "power_mode": "normal",
        "last_maintenance": "2026-01-18T12:00:00Z",
        "firmware_version": "3.2.1"
    }
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tower configuration tools"""
    return [
        Tool(
            name="get_tower_config",
            description="Get configuration details for a specific tower or all towers. Includes capacity, TRX count, antenna count, frequency bands, and power mode.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Tower ID (e.g., 'tower-001'). If not provided, returns all towers."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_towers_by_region",
            description="Get all towers in a specific region.",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Region ID (e.g., 'region-a' or 'region-b')"
                    }
                },
                "required": ["region"]
            }
        ),
        Tool(
            name="set_power_mode",
            description="Set the power mode for a tower. Options: 'normal', 'eco' (reduced power), 'boost' (max power), 'standby' (minimal power).",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Tower ID to configure"
                    },
                    "power_mode": {
                        "type": "string",
                        "enum": ["normal", "eco", "boost", "standby"],
                        "description": "Power mode to set"
                    }
                },
                "required": ["tower_id", "power_mode"]
            }
        ),
        Tool(
            name="set_active_trx",
            description="Set the number of active TRX (transmitters) on a tower. Used for energy optimization - reduce TRX during low demand.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Tower ID to configure"
                    },
                    "active_trx_count": {
                        "type": "integer",
                        "description": "Number of TRX to keep active (1 to max TRX count)"
                    }
                },
                "required": ["tower_id", "active_trx_count"]
            }
        ),
        Tool(
            name="get_nearby_towers",
            description="Find towers near a given tower for load balancing purposes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Reference tower ID"
                    },
                    "max_distance_km": {
                        "type": "number",
                        "description": "Maximum distance in kilometers",
                        "default": 10
                    }
                },
                "required": ["tower_id"]
            }
        ),
        Tool(
            name="activate_warm_spare",
            description="Activate a warm spare tower or additional capacity for handling traffic surge.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Tower ID to activate warm spare"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for activation (e.g., 'traffic_surge', 'failover', 'scheduled_event')"
                    }
                },
                "required": ["tower_id", "reason"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    if name == "get_tower_config":
        tower_id = arguments.get("tower_id")
        if tower_id:
            if tower_id in TOWER_CONFIGS:
                return [TextContent(type="text", text=json.dumps(TOWER_CONFIGS[tower_id], indent=2))]
            else:
                return [TextContent(type="text", text=json.dumps({"error": f"Tower {tower_id} not found"}))]
        else:
            return [TextContent(type="text", text=json.dumps(TOWER_CONFIGS, indent=2))]
    
    elif name == "get_towers_by_region":
        region = arguments.get("region")
        regional_towers = {
            tid: config for tid, config in TOWER_CONFIGS.items()
            if config["region"] == region
        }
        return [TextContent(type="text", text=json.dumps(regional_towers, indent=2))]
    
    elif name == "set_power_mode":
        tower_id = arguments.get("tower_id")
        power_mode = arguments.get("power_mode")
        
        if tower_id not in TOWER_CONFIGS:
            return [TextContent(type="text", text=json.dumps({"error": f"Tower {tower_id} not found"}))]
        
        old_mode = TOWER_CONFIGS[tower_id]["power_mode"]
        TOWER_CONFIGS[tower_id]["power_mode"] = power_mode
        
        result = {
            "success": True,
            "tower_id": tower_id,
            "previous_mode": old_mode,
            "new_mode": power_mode,
            "timestamp": datetime.now().isoformat(),
            "estimated_power_change": {
                "normal": 0,
                "eco": -30,  # 30% reduction
                "boost": 20,  # 20% increase
                "standby": -70  # 70% reduction
            }.get(power_mode, 0)
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "set_active_trx":
        tower_id = arguments.get("tower_id")
        active_trx_count = arguments.get("active_trx_count")
        
        if tower_id not in TOWER_CONFIGS:
            return [TextContent(type="text", text=json.dumps({"error": f"Tower {tower_id} not found"}))]
        
        max_trx = TOWER_CONFIGS[tower_id]["trx_count"]
        if active_trx_count < 1 or active_trx_count > max_trx:
            return [TextContent(type="text", text=json.dumps({
                "error": f"active_trx_count must be between 1 and {max_trx}"
            }))]
        
        old_count = TOWER_CONFIGS[tower_id]["active_trx"]
        TOWER_CONFIGS[tower_id]["active_trx"] = active_trx_count
        
        result = {
            "success": True,
            "tower_id": tower_id,
            "previous_active_trx": old_count,
            "new_active_trx": active_trx_count,
            "max_trx": max_trx,
            "timestamp": datetime.now().isoformat(),
            "power_savings_percent": round((old_count - active_trx_count) / old_count * 25, 1) if old_count > active_trx_count else 0
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_nearby_towers":
        tower_id = arguments.get("tower_id")
        max_distance = arguments.get("max_distance_km", 10)
        
        if tower_id not in TOWER_CONFIGS:
            return [TextContent(type="text", text=json.dumps({"error": f"Tower {tower_id} not found"}))]
        
        # Simplified distance calculation (all towers considered "nearby" for demo)
        nearby = []
        ref_tower = TOWER_CONFIGS[tower_id]
        
        for tid, config in TOWER_CONFIGS.items():
            if tid != tower_id:
                # Simplified: just check same region first, then others
                distance = 5 if config["region"] == ref_tower["region"] else 8
                if distance <= max_distance:
                    nearby.append({
                        "tower_id": tid,
                        "name": config["name"],
                        "distance_km": distance,
                        "available_capacity": config["capacity"] - 200,  # Simulated
                        "status": config["status"]
                    })
        
        result = {
            "reference_tower": tower_id,
            "max_distance_km": max_distance,
            "nearby_towers": nearby
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "activate_warm_spare":
        tower_id = arguments.get("tower_id")
        reason = arguments.get("reason")
        
        if tower_id not in TOWER_CONFIGS:
            return [TextContent(type="text", text=json.dumps({"error": f"Tower {tower_id} not found"}))]
        
        config = TOWER_CONFIGS[tower_id]
        
        # Activate all TRX and set to boost mode
        old_active_trx = config["active_trx"]
        old_power_mode = config["power_mode"]
        
        config["active_trx"] = config["trx_count"]
        config["power_mode"] = "boost"
        
        result = {
            "success": True,
            "tower_id": tower_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "changes": {
                "active_trx": {"from": old_active_trx, "to": config["trx_count"]},
                "power_mode": {"from": old_power_mode, "to": "boost"}
            },
            "estimated_capacity_increase": round((config["trx_count"] - old_active_trx) / config["trx_count"] * 100, 1),
            "message": f"Warm spare activated for {reason}"
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="trace://towers/all",
            name="All Tower Configurations",
            description="Complete configuration data for all towers",
            mimeType="application/json"
        ),
        Resource(
            uri="trace://towers/regions",
            name="Towers by Region",
            description="Towers grouped by region",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI"""
    if uri == "trace://towers/all":
        return json.dumps(TOWER_CONFIGS, indent=2)
    elif uri == "trace://towers/regions":
        regions = {}
        for tid, config in TOWER_CONFIGS.items():
            region = config["region"]
            if region not in regions:
                regions[region] = []
            regions[region].append(config)
        return json.dumps(regions, indent=2)
    else:
        return json.dumps({"error": f"Unknown resource: {uri}"})


async def main():
    """Run the MCP server"""
    logger.info("Starting TRACE Tower Config MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
