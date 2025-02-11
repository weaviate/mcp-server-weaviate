from typing import Optional
import weaviate
from weaviate.auth import Auth


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
        self._store_collection_name = store_collection_name

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

    async def store_memory(self, information: str):
        """
        Store a memory in the Weaviate store collection.
        :param information: The information to store.
        """
        self._client.data.insert(
            collection_name=self._store_collection_name,
            properties={
                "content": information
            }
        )

    async def find_memories(self, query: str) -> list[str]:
        """
        Find memories in the Weaviate search collection. If there are no memories found, an empty list is returned.
        :param query: The query to use for the search.
        :return: A list of memories found.
        """
        try:
            result = (
                self._client.query
                .get(self._search_collection_name, ["content"])
                .with_near_text({"concepts": [query]})
                .with_limit(10)
                .do()
            )
            
            if result and "data" in result:
                objects = result["data"]["Get"][self._search_collection_name]
                return [obj["content"] for obj in objects]
            return []
            
        except Exception:
            # Return empty list if collection doesn't exist or other errors
            return []