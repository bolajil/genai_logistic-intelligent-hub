"""ChromaDB vector store implementation."""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging

from .base import VectorStoreBase

logger = logging.getLogger(__name__)


class ChromaDBStore(VectorStoreBase):
    """ChromaDB implementation of vector store."""
    
    def __init__(self, config: Dict[str, Any], embedding_function):
        super().__init__(config, embedding_function)
        
        chromadb_config = config.get('vector_store', {}).get('chromadb', {})
        persist_dir = chromadb_config.get('persist_directory', 'data/chromadb')
        
        self.client = chromadb.Client(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False
        ))
        
        logger.info(f"ChromaDB initialized with persist_directory: {persist_dir}")
    
    def create_collection(self, collection_name: str, **kwargs) -> bool:
        """Create a new collection."""
        try:
            self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata=kwargs.get('metadata', {})
            )
            logger.info(f"Created collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """Add documents to a collection."""
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to {collection_name}: {e}")
            return False
    
    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        max_distance: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Query documents from a collection."""
        try:
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                result = {
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                }
                
                # Filter by max_distance if specified
                if max_distance is None or (result['distance'] is not None and result['distance'] <= max_distance):
                    formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to query {collection_name}: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()
            
            return {
                'name': collection_name,
                'count': count,
                'provider': 'chromadb'
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return {'name': collection_name, 'count': 0, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if ChromaDB is healthy."""
        try:
            collections = self.client.list_collections()
            return {
                'status': 'healthy',
                'provider': 'chromadb',
                'collections_count': len(collections)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'chromadb',
                'error': str(e)
            }
