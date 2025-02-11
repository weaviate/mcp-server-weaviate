import json
from typing import Any, Sequence

import weaviate
from pydantic import BaseModel, ValidationError, AnyUrl

import mcp.types as types
from mcp.server import Server

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

app = Server("weaviate-search-server")
_weaviate_client: weaviate.Client = None
_server_settings: Any = None

@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="weaviate_search",
            description="Perform a search query against a Weaviate vector database.",
            arguments=[
                types.PromptArgument(
                    name="query_params",
                    description=(
                        "A JSON object containing the following keys:\n"
                        "- target_collection (str): Name of the collection\n"
                        "- search_query (str): The text to search\n"
                        "- limit (int, optional): Max results to return (default 5)\n"
                        "- return_properties (list[str], optional): Properties to return"
                    ),
                    required=True,
                )
            ],
        )
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    if name == "weaviate_search":
        try:
            query_input = QueryWeaviateInput.model_validate(arguments)
        except ValidationError as e:
            raise ValueError(f"Invalid prompt arguments: {e}")

        prompt_text = f"""
You are a Weaviate search assistant.
Use the following search parameters to query the Weaviate database:
{json.dumps(query_input.model_dump(), indent=2)}

Respond with the search results in a clear and human-readable format.
        """
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=prompt_text)
                )
            ]
        )
    raise ValueError(f"Unknown prompt name: {name}")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_weaviate",
            description="Execute a search (hybrid) query against a Weaviate vector database.",
            inputSchema=QueryWeaviateInput.model_json_schema(),
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[types.TextContent]:
    if arguments is None:
        arguments = {}

    try:
        if name == "search_weaviate":
            args = QueryWeaviateInput.model_validate(arguments)
            collection = _weaviate_client.collections.get(args.target_collection)
            result = collection.query.hybrid(
                query=args.search_query,
                limit=args.limit,
                return_properties=args.return_properties,
            )
            formatted_result = _format_query_result(result)
            result_json = json.dumps({"result": formatted_result}, indent=2)
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    except ValidationError as e:
        await app.request_context.session.send_log_message("error", f"Validation error: {e}")
        return [types.TextContent(type="text", text=f"ERROR: {e}")]

    return [types.TextContent(type="text", text=result_json)]

async def run_stdio(settings: Any, weaviate_client: weaviate.Client):
    """
    Run the server on Standard I/O with the provided settings and Weaviate client.
    """
    from mcp.server.stdio import stdio_server

    global _weaviate_client
    _weaviate_client = weaviate_client

    global _server_settings
    _server_settings = settings

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
