"""Multi-vector database support for GLIH."""

from .base import VectorStoreBase
from .factory import get_vector_store

__all__ = ['VectorStoreBase', 'get_vector_store']
