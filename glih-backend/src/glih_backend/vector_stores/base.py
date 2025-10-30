"""Base interface for vector stores."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorStoreBase(ABC):
    """Abstract base class for vector store implementations."""
    
    def __init__(self, config: Dict[str, Any], embedding_function):
        self.config = config
        self.embedding_function = embedding_function
    
    @abstractmethod
    def create_collection(self, collection_name: str, **kwargs) -> bool:
        """Create a new collection/index."""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection/index."""
        pass
    
    @abstractmethod
    def list_collections(self) -> List[str]:
        """List all collections/indexes."""
        pass
    
    @abstractmethod
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """Add documents to a collection."""
        pass
    
    @abstractmethod
    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        max_distance: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Query documents from a collection."""
        pass
    
    @abstractmethod
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check if the vector store is healthy."""
        pass
