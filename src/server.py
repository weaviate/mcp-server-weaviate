import asyncio
import json
import logging
from typing import Any, Dict

import weaviate
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("mcp_weaviate")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)


class QueryWeaviateInput(BaseModel):
    target_collection: str
    search_query: str
    limit: int = 5
    return_properties: list[str] | None = None


def _format_query_result(result: Any) -> str:
    """Format query results into a readable string."""
    if hasattr(result, "objects"):
        formatted = "Found objects:\n"
        for obj in result.objects:
            formatted += "-" * 40 + "\n"
            for key, value in obj.properties.items():
                formatted += f"{key}: {value}\n"
        if hasattr(result, "total_count"):
            formatted += f"\nTotal matching results: {result.total_count}\n"
        return formatted
    return str(result)


async def main(weaviate_url: str, weaviate_api_key: str, openai_api_key: str):
    logger.info(f"Connecting to Weaviate at {weaviate_url}...")
    weaviate_client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
        headers={"X-OpenAI-Api-Key": openai_api_key},
    )
    logger.info("Connected to Weaviate.")

    server = Server("weaviate-manager")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools."""
        return [
            types.Tool(
                name="search-weaviate",
                description="Execute a hybrid search query against a Weaviate vector database.",
                inputSchema=QueryWeaviateInput.model_json_schema(),
            )
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: Dict[str, Any] | None
    ) -> list[types.TextContent]:
        """Handle tool execution requests."""
        try:
            if name == "search-weaviate":
                if arguments is None:
                    arguments = {}
                args = QueryWeaviateInput.model_validate(arguments)
                logger.debug(
                    f"Executing search on collection '{args.target_collection}' with query '{args.search_query}'"
                )
                collection = weaviate_client.collections.get(args.target_collection)
                result = collection.query.hybrid(
                    query=args.search_query,
                    limit=args.limit,
                    return_properties=args.return_properties,
                )
                formatted_result = _format_query_result(result)
                response_json = json.dumps({"result": formatted_result}, indent=2)
                return [types.TextContent(type="text", text=response_json)]
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return [types.TextContent(type="text", text=f"ERROR: {ve}")]
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Weaviate MCP server running with stdio transport")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="weaviate-manager",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )