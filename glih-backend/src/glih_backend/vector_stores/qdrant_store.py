"""Qdrant vector store implementation."""

import os
from typing import List, Dict, Any, Optional
import logging
import uuid

from .base import VectorStoreBase

logger = logging.getLogger(__name__)


class QdrantStore(VectorStoreBase):
    """Qdrant implementation of vector store."""
    
    def __init__(self, config: Dict[str, Any], embedding_function):
        super().__init__(config, embedding_function)
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
            self.QdrantClient = QdrantClient
            self.Distance = Distance
            self.VectorParams = VectorParams
            self.PointStruct = PointStruct
        except ImportError:
            raise ImportError("qdrant-client is not installed. Install with: pip install qdrant-client")
        
        qdrant_config = config.get('vector_store', {}).get('qdrant', {})
        
        url = qdrant_config.get('url', 'http://localhost:6333')
        api_key_env = qdrant_config.get('api_key_env', 'QDRANT_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if api_key:
            self.client = self.QdrantClient(url=url, api_key=api_key)
        else:
            self.client = self.QdrantClient(url=url)
        
        self.distance_metric = qdrant_config.get('distance_metric', 'Cosine')
        
        # Map distance metric names
        distance_map = {
            'Cosine': self.Distance.COSINE,
            'Euclid': self.Distance.EUCLID,
            'Dot': self.Distance.DOT
        }
        self.distance = distance_map.get(self.distance_metric, self.Distance.COSINE)
        
        logger.info(f"Qdrant initialized with URL: {url}")
    
    def create_collection(self, collection_name: str, **kwargs) -> bool:
        """Create a new collection."""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                logger.warning(f"Collection {collection_name} already exists")
                return True
            
            # We'll create the collection when first document is added
            # because we need to know the vector dimension
            logger.info(f"Collection {collection_name} will be created on first document add")
            return True
        except Exception as e:
            logger.error(f"Failed to check collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted Qdrant collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.get_collections().collections
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
            # Generate embeddings
            embeddings = []
            for doc in documents:
                emb = self.embedding_function([doc])[0]
                embeddings.append(emb)
            
            # Create collection if it doesn't exist
            collections = self.client.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                vector_size = len(embeddings[0])
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=self.VectorParams(size=vector_size, distance=self.distance)
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            
            # Prepare points
            points = []
            for i, (doc, emb) in enumerate(zip(documents, embeddings)):
                point_id = ids[i] if ids else str(uuid.uuid4())
                metadata = metadatas[i] if metadatas else {}
                metadata['document'] = doc  # Store document in payload
                
                points.append(
                    self.PointStruct(
                        id=point_id,
                        vector=emb,
                        payload=metadata
                    )
                )
            
            # Upsert points
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Added {len(documents)} documents to Qdrant collection {collection_name}")
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
            # Check if collection exists
            collections = self.client.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                logger.error(f"Collection {collection_name} not found")
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_function([query_text])[0]
            
            # Build filter if where is specified
            query_filter = None
            if where:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                conditions = []
                for key, value in where.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                query_filter = Filter(must=conditions)
            
            # Search
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=n_results,
                query_filter=query_filter
            )
            
            # Format results
            formatted_results = []
            for hit in search_result:
                distance = hit.score
                
                # Filter by max_distance if specified
                if max_distance is not None and distance > max_distance:
                    continue
                
                payload = hit.payload
                document = payload.pop('document', '')
                
                result = {
                    'id': str(hit.id),
                    'document': document,
                    'metadata': payload,
                    'distance': distance,
                    'score': hit.score
                }
                
                formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to query {collection_name}: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                return {'name': collection_name, 'count': 0, 'error': 'Collection not found'}
            
            collection_info = self.client.get_collection(collection_name=collection_name)
            
            return {
                'name': collection_name,
                'count': collection_info.points_count,
                'provider': 'qdrant',
                'vector_size': collection_info.config.params.vectors.size
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return {'name': collection_name, 'count': 0, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Qdrant is healthy."""
        try:
            collections = self.client.get_collections().collections
            return {
                'status': 'healthy',
                'provider': 'qdrant',
                'collections_count': len(collections)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'qdrant',
                'error': str(e)
            }
