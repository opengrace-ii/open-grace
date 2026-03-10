"""
Vector Store - Embedding-based memory for semantic search.

Supports FAISS (local, fast) and Chroma (persistent, feature-rich) backends.
Enables RAG (Retrieval Augmented Generation) for the AI system.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import numpy as np


@dataclass
class Document:
    """A document in the vector store."""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """Result from a vector search."""
    document: Document
    score: float
    rank: int


class EmbeddingProvider:
    """Base class for embedding providers."""
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        raise NotImplementedError
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        embeddings = self.embed([text])
        return embeddings[0] if embeddings else []


class SentenceTransformerProvider(EmbeddingProvider):
    """Embedding provider using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
        except ImportError:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Embedding provider using Ollama's embedding API."""
    
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.dimension = 768  # Depends on model
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama."""
        import requests
        
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                    timeout=30
                )
                response.raise_for_status()
                embedding = response.json().get("embedding", [])
                embeddings.append(embedding)
            except Exception as e:
                print(f"Embedding error: {e}")
                embeddings.append([])
        
        return embeddings


class VectorStore:
    """
    Vector store for semantic document storage and retrieval.
    
    Supports multiple backends:
    - FAISS: Fast, in-memory, good for local deployments
    - Chroma: Persistent, metadata-rich, good for production
    
    Usage:
        store = VectorStore(backend="faiss", embedding_provider=provider)
        store.add_document("doc1", "This is a document about AI")
        results = store.search("artificial intelligence", top_k=5)
    """
    
    def __init__(self, 
                 backend: str = "faiss",
                 embedding_provider: Optional[EmbeddingProvider] = None,
                 storage_path: Optional[str] = None,
                 dimension: int = 384):
        """
        Initialize the vector store.
        
        Args:
            backend: "faiss" or "chroma"
            embedding_provider: Provider for generating embeddings
            storage_path: Path for persistent storage
            dimension: Embedding dimension
        """
        self.backend = backend
        self.dimension = dimension
        self.storage_path = storage_path or os.path.expanduser("~/.open_grace/vector_store")
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding provider
        if embedding_provider is None:
            try:
                self.embedding_provider = SentenceTransformerProvider()
                self.dimension = self.embedding_provider.dimension
            except ImportError:
                print("Warning: sentence-transformers not available, using Ollama")
                self.embedding_provider = OllamaEmbeddingProvider()
        else:
            self.embedding_provider = embedding_provider
            if hasattr(embedding_provider, 'dimension'):
                self.dimension = embedding_provider.dimension
        
        # Initialize backend
        self._index = None
        self._documents: Dict[str, Document] = {}
        self._init_backend()
    
    def _init_backend(self):
        """Initialize the vector backend."""
        if self.backend == "faiss":
            self._init_faiss()
        elif self.backend == "chroma":
            self._init_chroma()
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    def _init_faiss(self):
        """Initialize FAISS backend."""
        try:
            import faiss
            
            # Create index
            self._index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
            
            # Load existing documents if available
            self._load_faiss()
        except ImportError:
            raise ImportError("faiss-cpu not installed. Run: pip install faiss-cpu")
    
    def _init_chroma(self):
        """Initialize Chroma backend."""
        try:
            import chromadb
            
            self._chroma_client = chromadb.PersistentClient(path=self.storage_path)
            self._collection = self._chroma_client.get_or_create_collection(
                name="open_grace_memory",
                metadata={"hnsw:space": "cosine"}
            )
        except ImportError:
            raise ImportError("chromadb not installed. Run: pip install chromadb")
    
    def _load_faiss(self):
        """Load existing FAISS index."""
        index_path = Path(self.storage_path) / "faiss.index"
        docs_path = Path(self.storage_path) / "documents.json"
        
        if index_path.exists():
            try:
                import faiss
                self._index = faiss.read_index(str(index_path))
            except Exception as e:
                print(f"Warning: Could not load FAISS index: {e}")
        
        if docs_path.exists():
            try:
                with open(docs_path) as f:
                    docs_data = json.load(f)
                    self._documents = {
                        k: Document(**v) for k, v in docs_data.items()
                    }
            except Exception as e:
                print(f"Warning: Could not load documents: {e}")
    
    def _save_faiss(self):
        """Save FAISS index and documents."""
        if self.backend != "faiss":
            return
        
        index_path = Path(self.storage_path) / "faiss.index"
        docs_path = Path(self.storage_path) / "documents.json"
        
        try:
            import faiss
            faiss.write_index(self._index, str(index_path))
            
            docs_data = {
                k: {
                    "id": v.id,
                    "content": v.content,
                    "metadata": v.metadata,
                    "created_at": v.created_at
                }
                for k, v in self._documents.items()
            }
            with open(docs_path, 'w') as f:
                json.dump(docs_data, f)
        except Exception as e:
            print(f"Warning: Could not save FAISS index: {e}")
    
    def add_document(self, doc_id: str, content: str, 
                     metadata: Optional[Dict[str, Any]] = None) -> Document:
        """
        Add a document to the store.
        
        Args:
            doc_id: Unique document ID
            content: Document content
            metadata: Optional metadata
            
        Returns:
            The created Document
        """
        # Generate embedding
        embedding = self.embedding_provider.embed_query(content)
        
        # Create document
        doc = Document(
            id=doc_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        # Add to backend
        if self.backend == "faiss":
            self._add_to_faiss(doc)
        elif self.backend == "chroma":
            self._add_to_chroma(doc)
        
        self._documents[doc_id] = doc
        return doc
    
    def _add_to_faiss(self, doc: Document):
        """Add document to FAISS index."""
        if doc.embedding:
            import faiss
            vector = np.array([doc.embedding], dtype=np.float32)
            # Normalize for cosine similarity
            faiss.normalize_L2(vector)
            self._index.add(vector)
    
    def _add_to_chroma(self, doc: Document):
        """Add document to Chroma collection."""
        self._collection.add(
            ids=[doc.id],
            documents=[doc.content],
            metadatas=[doc.metadata or {}]
        )
    
    def add_documents(self, documents: List[tuple]) -> List[Document]:
        """
        Add multiple documents efficiently.
        
        Args:
            documents: List of (doc_id, content, metadata) tuples
            
        Returns:
            List of created Documents
        """
        results = []
        
        # Generate embeddings in batch
        contents = [d[1] for d in documents]
        embeddings = self.embedding_provider.embed(contents)
        
        for (doc_id, content, metadata), embedding in zip(documents, embeddings):
            doc = Document(
                id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata or {}
            )
            
            if self.backend == "faiss":
                self._add_to_faiss(doc)
            
            self._documents[doc_id] = doc
            results.append(doc)
        
        if self.backend == "chroma":
            # Batch add to Chroma
            self._collection.add(
                ids=[d.id for d in results],
                documents=[d.content for d in results],
                metadatas=[d.metadata or {} for d in results]
            )
        
        if self.backend == "faiss":
            self._save_faiss()
        
        return results
    
    def search(self, query: str, top_k: int = 5, 
               filter_metadata: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of SearchResult
        """
        if self.backend == "faiss":
            return self._search_faiss(query, top_k)
        elif self.backend == "chroma":
            return self._search_chroma(query, top_k, filter_metadata)
        return []
    
    def _search_faiss(self, query: str, top_k: int) -> List[SearchResult]:
        """Search using FAISS."""
        import faiss
        
        # Generate query embedding
        query_embedding = self.embedding_provider.embed_query(query)
        query_vector = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vector)
        
        # Search
        scores, indices = self._index.search(query_vector, min(top_k, len(self._documents)))
        
        # Map to documents
        results = []
        doc_list = list(self._documents.values())
        
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx >= 0 and idx < len(doc_list):
                results.append(SearchResult(
                    document=doc_list[idx],
                    score=float(score),
                    rank=rank + 1
                ))
        
        return results
    
    def _search_chroma(self, query: str, top_k: int,
                       filter_metadata: Optional[Dict[str, Any]]) -> List[SearchResult]:
        """Search using Chroma."""
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filter_metadata
        )
        
        search_results = []
        if results['ids']:
            for rank, (doc_id, content, metadata, distance) in enumerate(zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                doc = Document(
                    id=doc_id,
                    content=content,
                    metadata=metadata or {}
                )
                # Convert distance to similarity score
                score = 1.0 - distance
                search_results.append(SearchResult(
                    document=doc,
                    score=score,
                    rank=rank + 1
                ))
        
        return search_results
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self._documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document."""
        if doc_id not in self._documents:
            return False
        
        del self._documents[doc_id]
        
        if self.backend == "chroma":
            self._collection.delete(ids=[doc_id])
        elif self.backend == "faiss":
            # FAISS doesn't support deletion easily, rebuild index
            self._rebuild_faiss_index()
        
        return True
    
    def _rebuild_faiss_index(self):
        """Rebuild FAISS index after deletion."""
        import faiss
        
        self._index = faiss.IndexFlatIP(self.dimension)
        for doc in self._documents.values():
            if doc.embedding:
                vector = np.array([doc.embedding], dtype=np.float32)
                faiss.normalize_L2(vector)
                self._index.add(vector)
        
        self._save_faiss()
    
    def clear(self):
        """Clear all documents."""
        self._documents.clear()
        
        if self.backend == "faiss":
            import faiss
            self._index = faiss.IndexFlatIP(self.dimension)
            self._save_faiss()
        elif self.backend == "chroma":
            self._collection.delete(where={})
    
    def count(self) -> int:
        """Get document count."""
        return len(self._documents)
    
    def save(self):
        """Save the store."""
        if self.backend == "faiss":
            self._save_faiss()


# Global store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def set_vector_store(store: VectorStore):
    """Set the global vector store instance."""
    global _vector_store
    _vector_store = store