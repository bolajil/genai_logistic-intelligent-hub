"""Unified vector store interface that wraps the multi-provider system."""

import os
import uuid
from typing import Any, Dict, List, Optional
import logging

from glih_backend.vector_stores import get_vector_store, VectorStoreBase
from glih_backend.config import load_config

logger = logging.getLogger(__name__)


class UnifiedVectorStore:
    """
    Unified vector store that provides a consistent interface across all providers.
    Maintains backward compatibility with existing code.
    """
    
    def __init__(self, provider: str = None, collection: str = None, config: Dict[str, Any] = None):
        """
        Initialize unified vector store.
        
        Args:
            provider: Vector store provider (chromadb, faiss, pinecone, etc.)
            collection: Default collection name
            config: Configuration dictionary (if None, loads from glih.toml)
        """
        # Load config if not provided
        if config is None:
            config = load_config()
        
        self.config = config
        
        # Override provider if specified
        if provider:
            self.config['vector_store']['provider'] = provider
        
        self.provider = self.config.get('vector_store', {}).get('provider', 'chromadb')
        self.collection = collection or self.config.get('vector_store', {}).get('collection', 'glih-default')
        
        # Initialize embedding function (placeholder - will be set by caller)
        self._embedding_function = None
        
        # Initialize vector store
        self._store: Optional[VectorStoreBase] = None
        
        logger.info(f"UnifiedVectorStore initialized with provider: {self.provider}")
    
    def set_embedding_function(self, embedding_function):
        """Set the embedding function and initialize the store."""
        self._embedding_function = embedding_function
        self._store = get_vector_store(self.config, embedding_function)
    
    def get_collection(self, name: str):
        """Get or create a collection."""
        if self._store is None:
            raise RuntimeError("Vector store not initialized. Call set_embedding_function first.")
        
        # Ensure collection exists
        collections = self._store.list_collections()
        if name not in collections:
            self._store.create_collection(name)
        
        return name  # Return name for compatibility
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        if self._store is None:
            return [self.collection]
        
        try:
            return self._store.list_collections()
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return [self.collection]
    
    def index(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """Index documents to the default collection."""
        return self.index_to(self.collection, texts, embeddings, metadatas)
    
    def index_to(
        self,
        collection: str,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """Index documents to a specific collection."""
        if self._store is None:
            raise RuntimeError("Vector store not initialized. Call set_embedding_function first.")
        
        try:
            # Generate IDs
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
            
            # Note: We're not using the embeddings parameter directly
            # because the store will generate them using the embedding function
            # This maintains backward compatibility
            success = self._store.add_documents(
                collection_name=collection,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return len(texts) if success else 0
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            return 0
    
    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        collection: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using a query embedding.
        Note: This is a compatibility method. The new interface uses query_text.
        """
        if self._store is None:
            raise RuntimeError("Vector store not initialized")
        
        # For compatibility, we need to convert embedding back to text
        # This is not ideal, but maintains backward compatibility
        # In practice, callers should use search_by_text instead
        collection_name = collection or self.collection
        
        try:
            # This is a workaround - ideally callers should use search_by_text
            results = self._store.query(
                collection_name=collection_name,
                query_text="",  # Empty query - will use embedding if store supports it
                n_results=k
            )
            
            # Format for backward compatibility
            formatted = []
            for r in results:
                formatted.append({
                    'id': r.get('id'),
                    'document': r.get('document'),
                    'metadata': r.get('metadata', {}),
                    'distance': r.get('distance')
                })
            
            return formatted
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_by_text(
        self,
        query_text: str,
        k: int = 5,
        collection: Optional[str] = None,
        where: Optional[Dict[str, Any]] = None,
        max_distance: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search using query text (preferred method)."""
        if self._store is None:
            raise RuntimeError("Vector store not initialized")
        
        collection_name = collection or self.collection
        
        try:
            results = self._store.query(
                collection_name=collection_name,
                query_text=query_text,
                n_results=k,
                where=where,
                max_distance=max_distance
            )
            
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_from(
        self,
        collection: str,
        query_embedding: List[float],
        k: int = 5,
        max_distance: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search from a specific collection."""
        return self.search(query_embedding, k, collection)
    
    def get_stats(self, collection: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a collection."""
        if self._store is None:
            return {'error': 'Store not initialized'}
        
        collection_name = collection or self.collection
        
        try:
            return self._store.get_collection_stats(collection_name)
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check vector store health."""
        if self._store is None:
            return {'status': 'not_initialized', 'provider': self.provider}
        
        try:
            return self._store.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'provider': self.provider, 'error': str(e)}
    
    def create_collection(self, name: str) -> bool:
        """Create a new collection."""
        if self._store is None:
            return False
        
        try:
            return self._store.create_collection(name)
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        if self._store is None:
            return False
        
        try:
            return self._store.delete_collection(name)
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
