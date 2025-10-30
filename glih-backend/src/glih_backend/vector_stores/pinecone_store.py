"""Pinecone vector store implementation."""

import os
from typing import List, Dict, Any, Optional
import logging
import uuid

from .base import VectorStoreBase

logger = logging.getLogger(__name__)


class PineconeStore(VectorStoreBase):
    """Pinecone implementation of vector store."""
    
    def __init__(self, config: Dict[str, Any], embedding_function):
        super().__init__(config, embedding_function)
        
        try:
            import pinecone
            self.pinecone = pinecone
        except ImportError:
            raise ImportError("pinecone-client is not installed. Install with: pip install pinecone-client")
        
        pinecone_config = config.get('vector_store', {}).get('pinecone', {})
        
        api_key_env = pinecone_config.get('api_key_env', 'PINECONE_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            raise ValueError(f"Pinecone API key not found in environment variable {api_key_env}")
        
        environment = pinecone_config.get('environment', 'us-east-1-aws')
        
        self.pinecone.init(api_key=api_key, environment=environment)
        
        self.index_name = pinecone_config.get('index_name', 'glih-index')
        self.dimension = pinecone_config.get('dimension', 1024)
        self.metric = pinecone_config.get('metric', 'cosine')
        self.pod_type = pinecone_config.get('pod_type', 'p1.x1')
        
        logger.info(f"Pinecone initialized with environment: {environment}")
    
    def create_collection(self, collection_name: str, **kwargs) -> bool:
        """Create a new index (collection in Pinecone terms)."""
        try:
            if collection_name not in self.pinecone.list_indexes():
                self.pinecone.create_index(
                    name=collection_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    pod_type=self.pod_type
                )
                logger.info(f"Created Pinecone index: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create index {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete an index."""
        try:
            self.pinecone.delete_index(collection_name)
            logger.info(f"Deleted Pinecone index: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all indexes."""
        try:
            return self.pinecone.list_indexes()
        except Exception as e:
            logger.error(f"Failed to list indexes: {e}")
            return []
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """Add documents to an index."""
        try:
            # Ensure index exists
            if collection_name not in self.pinecone.list_indexes():
                self.create_collection(collection_name)
            
            index = self.pinecone.Index(collection_name)
            
            # Generate embeddings
            embeddings = []
            for doc in documents:
                emb = self.embedding_function([doc])[0]
                embeddings.append(emb)
            
            # Prepare vectors for upsert
            vectors = []
            for i, (doc, emb) in enumerate(zip(documents, embeddings)):
                vector_id = ids[i] if ids else str(uuid.uuid4())
                metadata = metadatas[i] if metadatas else {}
                metadata['document'] = doc  # Store document in metadata
                
                vectors.append({
                    'id': vector_id,
                    'values': emb,
                    'metadata': metadata
                })
            
            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                index.upsert(vectors=batch)
            
            logger.info(f"Added {len(documents)} documents to Pinecone index {collection_name}")
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
        """Query documents from an index."""
        try:
            if collection_name not in self.pinecone.list_indexes():
                logger.error(f"Index {collection_name} not found")
                return []
            
            index = self.pinecone.Index(collection_name)
            
            # Generate query embedding
            query_embedding = self.embedding_function([query_text])[0]
            
            # Query
            results = index.query(
                vector=query_embedding,
                top_k=n_results,
                include_metadata=True,
                filter=where
            )
            
            # Format results
            formatted_results = []
            for match in results['matches']:
                score = match['score']
                
                # Convert score to distance (Pinecone returns similarity scores)
                if self.metric == 'cosine':
                    distance = 1 - score
                elif self.metric == 'dotproduct':
                    distance = -score
                else:  # euclidean
                    distance = score
                
                # Filter by max_distance if specified
                if max_distance is not None and distance > max_distance:
                    continue
                
                metadata = match.get('metadata', {})
                document = metadata.pop('document', '')
                
                result = {
                    'id': match['id'],
                    'document': document,
                    'metadata': metadata,
                    'distance': distance,
                    'score': score
                }
                
                formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to query {collection_name}: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about an index."""
        try:
            if collection_name not in self.pinecone.list_indexes():
                return {'name': collection_name, 'count': 0, 'error': 'Index not found'}
            
            index = self.pinecone.Index(collection_name)
            stats = index.describe_index_stats()
            
            return {
                'name': collection_name,
                'count': stats.get('total_vector_count', 0),
                'provider': 'pinecone',
                'dimension': stats.get('dimension', self.dimension)
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return {'name': collection_name, 'count': 0, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Pinecone is healthy."""
        try:
            indexes = self.pinecone.list_indexes()
            return {
                'status': 'healthy',
                'provider': 'pinecone',
                'collections_count': len(indexes)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'pinecone',
                'error': str(e)
            }
