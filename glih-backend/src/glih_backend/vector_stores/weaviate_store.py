"""Weaviate vector store implementation."""

import os
from typing import List, Dict, Any, Optional
import logging
import uuid

from .base import VectorStoreBase

logger = logging.getLogger(__name__)


class WeaviateStore(VectorStoreBase):
    """Weaviate implementation of vector store."""
    
    def __init__(self, config: Dict[str, Any], embedding_function):
        super().__init__(config, embedding_function)
        
        try:
            import weaviate
            self.weaviate = weaviate
        except ImportError:
            raise ImportError("weaviate-client is not installed. Install with: pip install weaviate-client")
        
        weaviate_config = config.get('vector_store', {}).get('weaviate', {})
        
        url = weaviate_config.get('url', 'http://localhost:8080')
        api_key_env = weaviate_config.get('api_key_env', 'WEAVIATE_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if api_key:
            self.client = weaviate.Client(
                url=url,
                auth_client_secret=weaviate.AuthApiKey(api_key=api_key)
            )
        else:
            self.client = weaviate.Client(url=url)
        
        self.class_name = weaviate_config.get('class_name', 'GlihDocument')
        self.distance_metric = weaviate_config.get('distance_metric', 'cosine')
        
        logger.info(f"Weaviate initialized with URL: {url}")
    
    def _sanitize_class_name(self, name: str) -> str:
        """Sanitize collection name to be a valid Weaviate class name."""
        # Weaviate class names must start with uppercase
        sanitized = ''.join(c if c.isalnum() else '_' for c in name)
        return sanitized[0].upper() + sanitized[1:] if sanitized else 'Collection'
    
    def create_collection(self, collection_name: str, **kwargs) -> bool:
        """Create a new class (collection in Weaviate terms)."""
        try:
            class_name = self._sanitize_class_name(collection_name)
            
            # Check if class already exists
            if self.client.schema.exists(class_name):
                logger.warning(f"Class {class_name} already exists")
                return True
            
            class_obj = {
                'class': class_name,
                'description': f'GLIH collection: {collection_name}',
                'vectorizer': 'none',  # We provide our own vectors
                'properties': [
                    {
                        'name': 'document',
                        'dataType': ['text'],
                        'description': 'The document content'
                    },
                    {
                        'name': 'metadata',
                        'dataType': ['text'],
                        'description': 'JSON metadata'
                    },
                    {
                        'name': 'original_id',
                        'dataType': ['text'],
                        'description': 'Original document ID'
                    }
                ]
            }
            
            self.client.schema.create_class(class_obj)
            logger.info(f"Created Weaviate class: {class_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create class {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a class."""
        try:
            class_name = self._sanitize_class_name(collection_name)
            self.client.schema.delete_class(class_name)
            logger.info(f"Deleted Weaviate class: {class_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete class {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all classes."""
        try:
            schema = self.client.schema.get()
            return [c['class'] for c in schema.get('classes', [])]
        except Exception as e:
            logger.error(f"Failed to list classes: {e}")
            return []
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """Add documents to a class."""
        try:
            class_name = self._sanitize_class_name(collection_name)
            
            # Ensure class exists
            if not self.client.schema.exists(class_name):
                self.create_collection(collection_name)
            
            # Add documents with batch
            with self.client.batch as batch:
                batch.batch_size = 100
                
                for i, doc in enumerate(documents):
                    # Generate embedding
                    embedding = self.embedding_function([doc])[0]
                    
                    # Prepare properties
                    properties = {
                        'document': doc,
                        'metadata': str(metadatas[i]) if metadatas else '{}',
                        'original_id': ids[i] if ids else str(uuid.uuid4())
                    }
                    
                    # Add to batch
                    batch.add_data_object(
                        data_object=properties,
                        class_name=class_name,
                        vector=embedding
                    )
            
            logger.info(f"Added {len(documents)} documents to Weaviate class {class_name}")
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
        """Query documents from a class."""
        try:
            class_name = self._sanitize_class_name(collection_name)
            
            if not self.client.schema.exists(class_name):
                logger.error(f"Class {class_name} not found")
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_function([query_text])[0]
            
            # Build query
            query_builder = (
                self.client.query
                .get(class_name, ['document', 'metadata', 'original_id'])
                .with_near_vector({'vector': query_embedding})
                .with_limit(n_results)
                .with_additional(['distance', 'id'])
            )
            
            # Execute query
            result = query_builder.do()
            
            # Format results
            formatted_results = []
            objects = result.get('data', {}).get('Get', {}).get(class_name, [])
            
            for obj in objects:
                distance = obj.get('_additional', {}).get('distance', 0)
                
                # Filter by max_distance if specified
                if max_distance is not None and distance > max_distance:
                    continue
                
                # Parse metadata
                import json
                try:
                    metadata = json.loads(obj.get('metadata', '{}'))
                except:
                    metadata = {}
                
                result_obj = {
                    'id': obj.get('original_id', obj.get('_additional', {}).get('id', '')),
                    'document': obj.get('document', ''),
                    'metadata': metadata,
                    'distance': distance
                }
                
                formatted_results.append(result_obj)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to query {collection_name}: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a class."""
        try:
            class_name = self._sanitize_class_name(collection_name)
            
            if not self.client.schema.exists(class_name):
                return {'name': collection_name, 'count': 0, 'error': 'Class not found'}
            
            # Get count
            result = self.client.query.aggregate(class_name).with_meta_count().do()
            count = result.get('data', {}).get('Aggregate', {}).get(class_name, [{}])[0].get('meta', {}).get('count', 0)
            
            return {
                'name': collection_name,
                'count': count,
                'provider': 'weaviate',
                'class_name': class_name
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return {'name': collection_name, 'count': 0, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Weaviate is healthy."""
        try:
            self.client.schema.get()
            schema = self.client.schema.get()
            return {
                'status': 'healthy',
                'provider': 'weaviate',
                'collections_count': len(schema.get('classes', []))
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'weaviate',
                'error': str(e)
            }
