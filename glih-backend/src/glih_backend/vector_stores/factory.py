"""Factory for creating vector store instances."""

from typing import Dict, Any
import logging

from .base import VectorStoreBase
from .chromadb_store import ChromaDBStore
from .faiss_store import FAISSStore
from .pinecone_store import PineconeStore
from .weaviate_store import WeaviateStore
from .qdrant_store import QdrantStore

logger = logging.getLogger(__name__)


def get_vector_store(config: Dict[str, Any], embedding_function) -> VectorStoreBase:
    """
    Factory function to get the appropriate vector store based on configuration.
    
    Args:
        config: Configuration dictionary
        embedding_function: Function to generate embeddings
    
    Returns:
        VectorStoreBase: Instance of the configured vector store
    
    Raises:
        ValueError: If provider is not supported
    """
    provider = config.get('vector_store', {}).get('provider', 'chromadb').lower()
    
    logger.info(f"Initializing vector store: {provider}")
    
    if provider == 'chromadb':
        return ChromaDBStore(config, embedding_function)
    elif provider == 'faiss':
        return FAISSStore(config, embedding_function)
    elif provider == 'pinecone':
        return PineconeStore(config, embedding_function)
    elif provider == 'weaviate':
        return WeaviateStore(config, embedding_function)
    elif provider == 'qdrant':
        return QdrantStore(config, embedding_function)
    elif provider == 'milvus':
        # Milvus implementation can be added later
        raise NotImplementedError("Milvus support coming soon")
    else:
        raise ValueError(f"Unsupported vector store provider: {provider}")


def get_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    Get information about available vector store providers.
    
    Returns:
        Dict with provider information
    """
    return {
        'chromadb': {
            'name': 'ChromaDB',
            'type': 'local',
            'description': 'Local persistent vector database',
            'requires': ['chromadb'],
            'features': ['local_storage', 'persistent', 'easy_setup']
        },
        'faiss': {
            'name': 'FAISS',
            'type': 'local',
            'description': 'Facebook AI Similarity Search - Fast local vector search',
            'requires': ['faiss-cpu'],  # or faiss-gpu
            'features': ['local_storage', 'fast_search', 'multiple_index_types']
        },
        'pinecone': {
            'name': 'Pinecone',
            'type': 'cloud',
            'description': 'Managed cloud vector database',
            'requires': ['pinecone-client'],
            'features': ['cloud_managed', 'scalable', 'real_time']
        },
        'weaviate': {
            'name': 'Weaviate',
            'type': 'cloud/self-hosted',
            'description': 'Open-source vector database with GraphQL API',
            'requires': ['weaviate-client'],
            'features': ['cloud_or_local', 'graphql', 'schema_support']
        },
        'qdrant': {
            'name': 'Qdrant',
            'type': 'cloud/self-hosted',
            'description': 'High-performance vector search engine',
            'requires': ['qdrant-client'],
            'features': ['cloud_or_local', 'fast', 'filtering']
        },
        'milvus': {
            'name': 'Milvus',
            'type': 'cloud/self-hosted',
            'description': 'Open-source vector database for AI applications',
            'requires': ['pymilvus'],
            'features': ['cloud_or_local', 'scalable', 'enterprise_ready'],
            'status': 'coming_soon'
        }
    }
