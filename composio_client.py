"""
Composio API v3 Client
Fetches and executes Composio tools dynamically
"""

import os
import logging
from typing import Dict, List, Any, Optional
import httpx

logger = logging.getLogger(__name__)

COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
COMPOSIO_API_BASE = "https://backend.composio.dev/api/v3"


class ComposioClient:
    """Client for Composio API v3"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or COMPOSIO_API_KEY
        self.base_url = COMPOSIO_API_BASE

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if not self.api_key:
            logger.warning("[Composio] API key not configured")
            return {}

        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def list_tools(self, page: int = 1, page_size: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch list of available Composio tools
        Returns: List of tool definitions with schemas
        """
        if not self.api_key:
            logger.warning("[Composio] Cannot list tools - API key not configured")
            return []

        try:
            url = f"{self.base_url}/tools"
            params = {
                "page": page,
                "pageSize": page_size
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                logger.info(f"[Composio] Raw API response keys: {list(data.keys())}")
                logger.info(f"[Composio] Response sample: {str(data)[:500]}")

                tools = data.get("data", [])
                if not tools and "items" in data:
                    tools = data.get("items", [])
                if not tools and isinstance(data, list):
                    tools = data

                logger.info(f"[Composio] Fetched {len(tools)} tools")

                return tools

        except httpx.HTTPStatusError as e:
            logger.error(f"[Composio] HTTP error fetching tools: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"[Composio] Error fetching tools: {e}", exc_info=True)
            return []

    async def get_tool_by_slug(self, tool_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific tool
        """
        if not self.api_key:
            logger.warning(f"[Composio] Cannot get tool {tool_slug} - API key not configured")
            return None

        try:
            url = f"{self.base_url}/tools/{tool_slug}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"[Composio] HTTP error fetching tool {tool_slug}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"[Composio] Error fetching tool {tool_slug}: {e}", exc_info=True)
            return None

    async def execute_tool(self, tool_slug: str, params: Dict[str, Any], connected_account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a Composio tool
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Composio API key not configured"
            }

        try:
            url = f"{self.base_url}/tools/execute/{tool_slug}"

            payload = {
                "input": params
            }

            if connected_account_id:
                payload["connectedAccountId"] = connected_account_id

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"[Composio] Tool {tool_slug} executed successfully")
                return {
                    "success": True,
                    "result": result
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"[Composio] HTTP error executing tool {tool_slug}: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"[Composio] Error executing tool {tool_slug}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def convert_to_mcp_schema(self, composio_tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Composio tool schema to MCP inputSchema format
        """
        return {
            "name": composio_tool.get("slug", composio_tool.get("name", "unknown")),
            "description": composio_tool.get("description", ""),
            "inputSchema": composio_tool.get("parameters", {
                "type": "object",
                "properties": {},
                "required": []
            })
        }


# Global instance
composio_client = ComposioClient()
