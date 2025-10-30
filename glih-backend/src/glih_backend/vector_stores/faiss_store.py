"""FAISS vector store implementation."""

import faiss
import numpy as np
import pickle
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import uuid

from .base import VectorStoreBase

logger = logging.getLogger(__name__)


class FAISSStore(VectorStoreBase):
    """FAISS implementation of vector store."""
    
    def __init__(self, config: Dict[str, Any], embedding_function):
        super().__init__(config, embedding_function)
        
        faiss_config = config.get('vector_store', {}).get('faiss', {})
        self.persist_dir = Path(faiss_config.get('persist_directory', 'data/faiss'))
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_type = faiss_config.get('index_type', 'IndexFlatL2')
        self.nlist = faiss_config.get('nlist', 100)
        self.m = faiss_config.get('m', 16)
        
        # Store for metadata and documents
        self.collections = {}
        self._load_collections()
        
        logger.info(f"FAISS initialized with persist_directory: {self.persist_dir}")
    
    def _get_collection_path(self, collection_name: str) -> Path:
        """Get path for collection files."""
        return self.persist_dir / collection_name
    
    def _load_collections(self):
        """Load existing collections from disk."""
        if not self.persist_dir.exists():
            return
        
        for collection_dir in self.persist_dir.iterdir():
            if collection_dir.is_dir():
                try:
                    self._load_collection(collection_dir.name)
                except Exception as e:
                    logger.error(f"Failed to load collection {collection_dir.name}: {e}")
    
    def _load_collection(self, collection_name: str):
        """Load a single collection."""
        collection_path = self._get_collection_path(collection_name)
        index_file = collection_path / "index.faiss"
        metadata_file = collection_path / "metadata.pkl"
        
        if not index_file.exists() or not metadata_file.exists():
            return
        
        # Load FAISS index
        index = faiss.read_index(str(index_file))
        
        # Load metadata
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        self.collections[collection_name] = {
            'index': index,
            'documents': metadata.get('documents', []),
            'metadatas': metadata.get('metadatas', []),
            'ids': metadata.get('ids', []),
            'dimension': index.d
        }
        
        logger.info(f"Loaded collection {collection_name} with {len(metadata.get('ids', []))} documents")
    
    def _save_collection(self, collection_name: str):
        """Save a collection to disk."""
        if collection_name not in self.collections:
            return False
        
        collection_path = self._get_collection_path(collection_name)
        collection_path.mkdir(parents=True, exist_ok=True)
        
        collection = self.collections[collection_name]
        
        # Save FAISS index
        index_file = collection_path / "index.faiss"
        faiss.write_index(collection['index'], str(index_file))
        
        # Save metadata
        metadata_file = collection_path / "metadata.pkl"
        metadata = {
            'documents': collection['documents'],
            'metadatas': collection['metadatas'],
            'ids': collection['ids']
        }
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Saved collection {collection_name}")
        return True
    
    def _create_index(self, dimension: int) -> faiss.Index:
        """Create a FAISS index based on configuration."""
        if self.index_type == 'IndexFlatL2':
            return faiss.IndexFlatL2(dimension)
        elif self.index_type == 'IndexIVFFlat':
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, self.nlist)
            return index
        elif self.index_type == 'IndexHNSW':
            index = faiss.IndexHNSWFlat(dimension, self.m)
            return index
        else:
            logger.warning(f"Unknown index type {self.index_type}, using IndexFlatL2")
            return faiss.IndexFlatL2(dimension)
    
    def create_collection(self, collection_name: str, **kwargs) -> bool:
        """Create a new collection."""
        try:
            if collection_name in self.collections:
                logger.warning(f"Collection {collection_name} already exists")
                return False
            
            # We'll create the index when first document is added
            self.collections[collection_name] = {
                'index': None,
                'documents': [],
                'metadatas': [],
                'ids': [],
                'dimension': None
            }
            
            logger.info(f"Created collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            if collection_name in self.collections:
                del self.collections[collection_name]
            
            # Delete from disk
            collection_path = self._get_collection_path(collection_name)
            if collection_path.exists():
                import shutil
                shutil.rmtree(collection_path)
            
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        return list(self.collections.keys())
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """Add documents to a collection."""
        try:
            # Create collection if it doesn't exist
            if collection_name not in self.collections:
                self.create_collection(collection_name)
            
            collection = self.collections[collection_name]
            
            # Generate embeddings
            embeddings = []
            for doc in documents:
                emb = self.embedding_function([doc])[0]
                embeddings.append(emb)
            
            embeddings_array = np.array(embeddings).astype('float32')
            
            # Create index if this is the first add
            if collection['index'] is None:
                dimension = embeddings_array.shape[1]
                collection['index'] = self._create_index(dimension)
                collection['dimension'] = dimension
                
                # Train index if needed
                if self.index_type == 'IndexIVFFlat':
                    collection['index'].train(embeddings_array)
            
            # Add to index
            collection['index'].add(embeddings_array)
            
            # Store documents and metadata
            collection['documents'].extend(documents)
            collection['metadatas'].extend(metadatas or [{} for _ in documents])
            collection['ids'].extend(ids or [str(uuid.uuid4()) for _ in documents])
            
            # Save to disk
            self._save_collection(collection_name)
            
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
            if collection_name not in self.collections:
                logger.error(f"Collection {collection_name} not found")
                return []
            
            collection = self.collections[collection_name]
            
            if collection['index'] is None or len(collection['ids']) == 0:
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_function([query_text])[0]
            query_array = np.array([query_embedding]).astype('float32')
            
            # Search
            distances, indices = collection['index'].search(query_array, min(n_results, len(collection['ids'])))
            
            # Format results
            formatted_results = []
            for i, idx in enumerate(indices[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue
                
                distance = float(distances[0][i])
                
                # Filter by max_distance if specified
                if max_distance is not None and distance > max_distance:
                    continue
                
                result = {
                    'id': collection['ids'][idx],
                    'document': collection['documents'][idx],
                    'metadata': collection['metadatas'][idx],
                    'distance': distance
                }
                
                # Apply metadata filter if specified
                if where:
                    matches = all(
                        result['metadata'].get(k) == v
                        for k, v in where.items()
                    )
                    if not matches:
                        continue
                
                formatted_results.append(result)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to query {collection_name}: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        try:
            if collection_name not in self.collections:
                return {'name': collection_name, 'count': 0, 'error': 'Collection not found'}
            
            collection = self.collections[collection_name]
            
            return {
                'name': collection_name,
                'count': len(collection['ids']),
                'provider': 'faiss',
                'index_type': self.index_type,
                'dimension': collection['dimension']
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return {'name': collection_name, 'count': 0, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if FAISS is healthy."""
        try:
            return {
                'status': 'healthy',
                'provider': 'faiss',
                'collections_count': len(self.collections),
                'index_type': self.index_type
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'faiss',
                'error': str(e)
            }
