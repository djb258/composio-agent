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
    Returns list of available tools with their schemas
    """
    return {
        "tools": [
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
            },
            {
                "name": "firebase_read",
                "description": "Read data from Firebase Realtime Database or Firestore",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Firebase path to read from"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "firebase_write",
                "description": "Write data to Firebase Realtime Database or Firestore",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Firebase path to write to"
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to write"
                        }
                    },
                    "required": ["path", "data"]
                }
            }
        ]
    }


async def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle tools/call request
    Execute a tool and return results
    """
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    logger.info(f"[MCP] Tool call: {tool_name}")

    # Import MCP server functions
    try:
        from mcp_server import (
            get_service_status,
            get_latest_deploy,
            get_logs,
            list_deploys,
            trigger_deploy
        )

        # Route to appropriate tool
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
        elif tool_name == "firebase_read":
            result = {
                "message": "Firebase read simulated",
                "path": arguments.get("path"),
                "data": {}
            }
        elif tool_name == "firebase_write":
            result = {
                "message": "Firebase write simulated",
                "path": arguments.get("path"),
                "success": True
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}"
                    }
                ],
                "isError": True
            }

        # Return MCP-compliant response
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result)
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
