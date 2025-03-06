from typing import Optional, Any
import weaviate
from weaviate.auth import Auth
from weaviate_agents.query import QueryAgent


class WeaviateConnector:
    """
    Encapsulates the connection to a Weaviate server and all the methods to interact with it.
    :param weaviate_url: The URL of the Weaviate server.
    :param weaviate_api_key: The API key to use for the Weaviate server.
    :param search_collection_name: The name of the collection to search from.
    :param store_collection_name: The name of the collection to store memories in.
    :param cohere_api_key: Optional API key to use Cohere embeddings.
    :param openai_api_key: Optional API key to use OpenAI embeddings.
    """

    def __init__(
        self,
        weaviate_url: Optional[str],
        weaviate_api_key: Optional[str],
        search_collection_name: str,
        store_collection_name: str,
        cohere_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        if not (cohere_api_key or openai_api_key):
            raise ValueError("Either a Cohere or OpenAI API key must be provided")

        self._weaviate_url = weaviate_url.rstrip("/") if weaviate_url else None
        self._weaviate_api_key = weaviate_api_key
        self._search_collection_name = search_collection_name
        self._knowledge_base_query_agent = QueryAgent(
            client=weaviate_client,
            collections=self._search_collection_name
        )
        self._store_collection_name = store_collection_name
        self._memories_query_agent = QueryAgent(
            client=weaviate_client,
            collections=[self._search_collection_name, self._store_collection_name]
        )

        headers = {}
        if cohere_api_key:
            headers["X-Cohere-Api-Key"] = cohere_api_key
        if openai_api_key:
            headers["X-OpenAI-Api-Key"] = openai_api_key

        self._client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
            headers=headers
        )

        # Store collections as instance variables
        self._search_collection = self._client.collections.get(search_collection_name)
        self._store_collection = self._client.collections.get(store_collection_name)

    async def store_memory(self, information: str):
        """
        Store a memory in the Weaviate store collection.
        :param information: The information to store.
        """
        self._store_collection.data.insert(
            properties={
                "content": information
            }
        )

    def _format_query_result(self, result: Any) -> str:
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

    async def find_memories(self, query: str) -> list[str]:
        """
        Find memories in the Weaviate store collection. If there are no memories found, an empty list is returned.
        :param query: The query to use for the search.
        :return: A list of memories found.
        """
        try:
            result = self._memories_query_agent.run(query).final_answer
            
        except Exception:
            # Return empty list if collection doesn't exist or other errors
            return []

    async def search_knowledge_base(self, query: str) -> list[str]:
        """
        Search the knowledge base in the Weaviate search collection. If there are no results found, an empty list is returned.
        :param query: The query to use for the search.
        :return: A list of relevant knowledge base entries found.
        """
        try:
            result = self._knowledge_base_query_agent.run(query).final_answer
            
        except Exception:
            # Return empty list if collection doesn't exist or other errors
            return []
