"""
JSON-RPC 2.0 Handler for MCP Protocol
Implements the Model Context Protocol specification for ChatGPT integration
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request"""
    jsonrpc: str = "2.0"
    id: Optional[int | str] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response"""
    jsonrpc: str = "2.0"
    id: Optional[int | str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


async def handle_jsonrpc_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming JSON-RPC 2.0 request according to MCP specification
    """
    try:
        # Parse JSON-RPC request
        req = JSONRPCRequest(**request_data)

        logger.info(f"[MCP] JSON-RPC method: {req.method}")

        # Route to appropriate handler
        if req.method == "initialize":
            result = await handle_initialize(req.params or {})
        elif req.method == "tools/list":
            result = await handle_tools_list(req.params or {})
        elif req.method == "tools/call":
            result = await handle_tools_call(req.params or {})
        elif req.method == "resources/list":
            result = await handle_resources_list(req.params or {})
        elif req.method == "prompts/list":
            result = await handle_prompts_list(req.params or {})
        else:
            # Method not found
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {req.method}"
                }
            }

        # Return successful response
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": result
        }

    except Exception as e:
        logger.error(f"[MCP] JSON-RPC error: {str(e)}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle MCP initialize request
    Returns server capabilities and info
    """
    logger.info(f"[MCP] Initialize request from: {params.get('clientInfo', {}).get('name', 'unknown')}")

    return {
        "protocolVersion": "2025-03-26",
        "capabilities": {
            "tools": {
                "listChanged": True
            },
            "resources": {
                "subscribe": False,
                "listChanged": False
            },
            "prompts": {
                "listChanged": False
            },
            "logging": {}
        },
        "serverInfo": {
            "name": "Composio Agent Gateway",
            "version": "1.0.0"
        },
        "instructions": "MCP server for Composio, Render, and Firebase tools. Use available tools to manage deployments, access Firebase data, and monitor services."
    }


async def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle tools/list request
    Returns list of available tools with their schemas from Composio + Render tools
    """
    logger.info("[MCP] tools/list called - fetching tools")
    tools = []

    # Add Render management tools
    render_tools = [
        {
            "name": "render_get_service_status",
            "description": "Get current status of Render service including deployment state",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "render_get_latest_deploy",
            "description": "Get information about the latest deployment",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "render_get_logs",
            "description": "Fetch recent logs from the Render service",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of log lines to fetch",
                        "default": 100
                    }
                },
                "required": []
            }
        },
        {
            "name": "render_list_deploys",
            "description": "List recent deployments",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of deployments to list",
                        "default": 10
                    }
                },
                "required": []
            }
        },
        {
            "name": "render_trigger_deploy",
            "description": "Trigger a new deployment with optional cache clear",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "clear_cache": {
                        "type": "boolean",
                        "description": "Whether to clear build cache",
                        "default": False
                    }
                },
                "required": []
            }
        }
    ]
    tools.extend(render_tools)

    # Fetch Composio tools dynamically
    logger.info("[MCP] Starting Composio tool fetch...")
    try:
        from composio_client import composio_client

        logger.info(f"[MCP] Composio API key configured: {bool(composio_client.api_key)}")

        composio_tools = await composio_client.list_tools(page=1, page_size=100)

        logger.info(f"[MCP] Received {len(composio_tools)} tools from Composio API")

        for tool in composio_tools:
            mcp_tool = composio_client.convert_to_mcp_schema(tool)
            tools.append(mcp_tool)

        logger.info(f"[MCP] ✅ Successfully loaded {len(render_tools)} Render tools + {len(composio_tools)} Composio tools")

    except Exception as e:
        logger.error(f"[MCP] ❌ Error loading Composio tools: {e}", exc_info=True)
        logger.info(f"[MCP] Continuing with {len(render_tools)} Render tools only")

    logger.info(f"[MCP] Returning total of {len(tools)} tools to client")
    return {"tools": tools}


async def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle tools/call request
    Execute a tool and return results
    """
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    logger.info(f"[MCP] Tool call: {tool_name}")

    try:
        # Check if this is a Render tool
        if tool_name.startswith("render_"):
            from mcp_server import (
                get_service_status,
                get_latest_deploy,
                get_logs,
                list_deploys,
                trigger_deploy
            )

            # Route to appropriate Render tool
            if tool_name == "render_get_service_status":
                result = await get_service_status()
            elif tool_name == "render_get_latest_deploy":
                result = await get_latest_deploy()
            elif tool_name == "render_get_logs":
                limit = arguments.get("limit", 100)
                result = await get_logs(limit)
            elif tool_name == "render_list_deploys":
                limit = arguments.get("limit", 10)
                result = await list_deploys(limit)
            elif tool_name == "render_trigger_deploy":
                clear_cache = arguments.get("clear_cache", False)
                result = await trigger_deploy(clear_cache)
            else:
                result = {"error": f"Unknown Render tool: {tool_name}"}

        else:
            # This is a Composio tool - execute via Composio API
            from composio_client import composio_client

            logger.info(f"[MCP] Executing Composio tool: {tool_name}")

            exec_result = await composio_client.execute_tool(
                tool_slug=tool_name,
                params=arguments
            )

            if exec_result.get("success"):
                result = exec_result.get("result", {})
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error executing Composio tool: {exec_result.get('error')}"
                        }
                    ],
                    "isError": True
                }

        # Return MCP-compliant response
        import json
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }

    except Exception as e:
        logger.error(f"[MCP] Tool execution error: {str(e)}", exc_info=True)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error executing tool: {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_resources_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle resources/list request"""
    return {"resources": []}


async def handle_prompts_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle prompts/list request"""
    return {"prompts": []}
