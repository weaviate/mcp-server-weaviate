from typing import Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions

import click
import mcp.types as types
import asyncio
import mcp

from .weaviate import WeaviateConnector

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def serve(
    weaviate_url: Optional[str],
    weaviate_api_key: Optional[str], 
    search_collection_name: str,
    store_collection_name: str,
    cohere_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
) -> Server:
    """
    Instantiate the server and configure tools to store and find memories in Weaviate.
    :param weaviate_url: The URL of the Weaviate server.
    :param weaviate_api_key: The API key to use for the Weaviate server.
    :param search_collection_name: The name of the collection to search from.
    :param store_collection_name: The name of the collection to store memories in.
    :param cohere_api_key: Optional API key to use Cohere embeddings.
    :param openai_api_key: Optional API key to use OpenAI embeddings.
    """
    server = Server("weaviate")

    weaviate = WeaviateConnector(
        weaviate_url, weaviate_api_key, search_collection_name, store_collection_name,
        cohere_api_key=cohere_api_key, openai_api_key=openai_api_key
    )

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """
        Return the list of tools that the server provides. By default, there are three
        tools: one to store memories, another to find them, and one to search the knowledge base.
        Finding the memories is not implemented as a resource, as it requires a query to be 
        passed and resources point to a very specific piece of data.
        """
        return [
            types.Tool(
                name="weaviate-store-memory",
                description=(
                    "Keep the memory for later use, when you are asked to remember something."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "information": {
                            "type": "string",
                        },
                    },
                    "required": ["information"],
                },
            ),
            types.Tool(
                name="weaviate-find-memories",
                description=(
                    "Look up memories in Weaviate. Use this tool when you need to: \n"
                    " - Find memories by their content \n"
                    " - Access memories for further analysis \n"
                    " - Get some personal information about the user"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to search for in the memories",
                        },
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="weaviate-search-knowledge",
                description=(
                    "Search the knowledge base in Weaviate. Use this tool when you need to: \n"
                    " - Find relevant information from the knowledge base \n"
                    " - Access structured knowledge \n"
                    " - Get factual information"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to search for in the knowledge base",
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_tool_call(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name not in ["weaviate-store-memory", "weaviate-find-memories", "weaviate-search-knowledge"]:
            raise ValueError(f"Unknown tool: {name}")

        if name == "weaviate-store-memory":
            if not arguments or "information" not in arguments:
                raise ValueError("Missing required argument 'information'")
            information = arguments["information"]
            await weaviate.store_memory(information)
            return [types.TextContent(type="text", text=f"Remembered: {information}")]

        if name == "weaviate-find-memories":
            if not arguments or "query" not in arguments:
                raise ValueError("Missing required argument 'query'")
            query = arguments["query"]
            memories = await weaviate.find_memories(query)
            content = [
                types.TextContent(
                    type="text", text=f"Memories for the query '{query}'"
                ),
            ]
            for memory in memories:
                content.append(
                    types.TextContent(type="text", text=f"<memory>{memory}</memory>")
                )
            return content

        if name == "weaviate-search-knowledge":
            if not arguments or "query" not in arguments:
                raise ValueError("Missing required argument 'query'")
            query = arguments["query"]
            results = await weaviate.search_knowledge_base(query)
            content = [
                types.TextContent(
                    type="text", text=f"Knowledge base results for the query '{query}'"
                ),
            ]
            for result in results:
                content.append(
                    types.TextContent(type="text", text=f"<result>{result}</result>")
                )
            return content

    return server


@click.command()
@click.option(
    "--weaviate-url",
    envvar="WEAVIATE_URL",
    required=False,
    help="Weaviate URL",
)
@click.option(
    "--weaviate-api-key",
    envvar="WEAVIATE_API_KEY", 
    required=False,
    help="Weaviate API key",
)
@click.option(
    "--search-collection-name",
    envvar="SEARCH_COLLECTION_NAME",
    required=True,
    help="Name of collection to search from",
)
@click.option(
    "--store-collection-name",
    envvar="STORE_COLLECTION_NAME",
    required=True,
    help="Name of collection to store memories in",
)
@click.option(
    "--cohere-api-key",
    envvar="COHERE_API_KEY",
    required=False,
    help="Cohere API key for embeddings",
)
@click.option(
    "--openai-api-key",
    envvar="OPENAI_API_KEY",
    required=False,
    help="OpenAI API key for embeddings",
)
def main(
    weaviate_url: Optional[str],
    weaviate_api_key: Optional[str],
    search_collection_name: str,
    store_collection_name: str,
    cohere_api_key: Optional[str],
    openai_api_key: Optional[str],
):
    if not (cohere_api_key or openai_api_key):
        raise ValueError("Either a Cohere or OpenAI API key must be provided")

    async def _run():
        logger.debug("Starting server...")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            server = serve(
                weaviate_url,
                weaviate_api_key,
                search_collection_name,
                store_collection_name,
                cohere_api_key,
                openai_api_key,
            )
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="weaviate",
                    server_version="0.0.1",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    asyncio.run(_run())

if __name__ == "__main__":
    print("Running main...", flush=True)
    main()