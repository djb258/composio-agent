"""
SSE (Server-Sent Events) Transport for MCP
Enables Claude Desktop to connect natively via SSE transport
"""

import json
import logging
import asyncio
from typing import AsyncIterator
from fastapi import Request
from fastapi.responses import StreamingResponse
from mcp_jsonrpc import handle_jsonrpc_request

logger = logging.getLogger(__name__)


async def sse_stream(request: Request) -> AsyncIterator[str]:
    """
    Generate Server-Sent Events stream for MCP protocol
    Implements bidirectional JSON-RPC over SSE
    """
    logger.info("[MCP SSE] Client connected")

    try:
        # Send initial connection established event
        yield f"event: endpoint\ndata: /message\n\n"

        # Keep connection alive and process messages
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("[MCP SSE] Client disconnected")
                break

            # Wait for incoming data (if any)
            # In SSE, client sends POST requests to /message endpoint
            # This stream just keeps the connection alive
            await asyncio.sleep(1)

            # Send keep-alive comment every 30 seconds
            yield ": keep-alive\n\n"

    except asyncio.CancelledError:
        logger.info("[MCP SSE] Stream cancelled")
    except Exception as e:
        logger.error(f"[MCP SSE] Error: {e}", exc_info=True)


async def handle_sse_message(request: Request) -> dict:
    """
    Handle incoming JSON-RPC message via SSE POST endpoint
    This is how Claude Desktop sends requests to the server
    """
    try:
        body = await request.json()
        logger.info(f"[MCP SSE] Received message: {body.get('method', 'unknown')}")

        # Handle JSON-RPC request
        response = await handle_jsonrpc_request(body)

        return response

    except Exception as e:
        logger.error(f"[MCP SSE] Message handling error: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


def create_sse_response(request: Request) -> StreamingResponse:
    """
    Create SSE StreamingResponse for MCP connection
    """
    return StreamingResponse(
        sse_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
