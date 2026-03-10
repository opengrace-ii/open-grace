"""
RAG Engine - Retrieval Augmented Generation for Open Grace.

Combines vector search with LLM generation to provide context-aware responses.
Enables the AI to search through documents, code, and knowledge bases.
"""

import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from open_grace.memory.vector_store import VectorStore, get_vector_store, SearchResult
from open_grace.memory.document_processor import DocumentProcessor, get_document_processor
from open_grace.model_router.router import ModelRouter, get_router


@dataclass
class RAGContext:
    """Context retrieved for RAG."""
    query: str
    documents: List[SearchResult]
    context_text: str
    total_tokens: int


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    answer: str
    context: RAGContext
    sources: List[Dict[str, Any]]
    model_used: str
    latency_ms: float


class RAGEngine:
    """
    Retrieval Augmented Generation engine.
    
    Provides context-aware AI responses by:
    1. Searching vector store for relevant documents
    2. Combining retrieved context with the query
    3. Generating response using LLM
    
    Usage:
        rag = RAGEngine()
        
        # Index documents
        rag.index_document("doc1", "Python is a programming language...")
        
        # Query with context
        response = rag.query("What is Python used for?")
        print(response.answer)
        print(f"Sources: {[s['id'] for s in response.sources]}")
    """
    
    def __init__(self, 
                 vector_store: Optional[VectorStore] = None,
                 model_router: Optional[ModelRouter] = None,
                 document_processor: Optional[DocumentProcessor] = None,
                 max_context_tokens: int = 4000,
                 top_k_documents: int = 5):
        """
        Initialize the RAG engine.
        
        Args:
            vector_store: Vector store for document retrieval
            model_router: Model router for generation
            max_context_tokens: Maximum tokens for context
            top_k_documents: Number of documents to retrieve
        """
        self.vector_store = vector_store or get_vector_store()
        self.model_router = model_router or get_router()
        self.document_processor = document_processor or get_document_processor()
        self.max_context_tokens = max_context_tokens
        self.top_k_documents = top_k_documents
        
        # Token estimation (rough approximation)
        self.tokens_per_char = 0.25
    
    def index_document(self, doc_id: str, content: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Index a document for retrieval.
        
        Args:
            doc_id: Unique document identifier
            content: Document content
            metadata: Optional metadata (source, type, etc.)
        """
        # Add timestamp to metadata
        meta = metadata or {}
        meta['indexed_at'] = datetime.now().isoformat()
        
        self.vector_store.add_document(doc_id, content, metadata=meta)
    
    def index_file(self, file_path: str, 
                   doc_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Index a file for retrieval.
        
        Supports: PDF, DOCX, DOC, XLSX, XLS, CSV, TXT, MD, and more.
        
        Args:
            file_path: Path to the file
            doc_id: Optional document ID (defaults to file path)
            metadata: Optional metadata
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use document processor to extract content
        extracted = self.document_processor.extract(file_path)
        content = extracted.text
        
        # Generate doc_id from path if not provided
        if doc_id is None:
            doc_id = str(path)
        
        # Add file metadata
        meta = metadata or {}
        meta.update({
            'source': str(path),
            'filename': path.name,
            'file_type': path.suffix,
            'file_size': path.stat().st_size,
        })
        
        # Add extraction metadata
        meta.update(extracted.metadata)
        
        self.index_document(doc_id, content, metadata=meta)
    
    def index_directory(self, dir_path: str, 
                        pattern: str = "*.txt",
                        recursive: bool = True) -> int:
        """
        Index all matching files in a directory.
        
        Args:
            dir_path: Directory path
            pattern: File pattern to match
            recursive: Whether to search recursively
            
        Returns:
            Number of files indexed
        """
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        count = 0
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))
        
        for file_path in files:
            try:
                self.index_file(str(file_path))
                count += 1
            except Exception as e:
                print(f"Warning: Could not index {file_path}: {e}")
        
        return count
    
    def retrieve_context(self, query: str, 
                         filter_metadata: Optional[Dict[str, Any]] = None) -> RAGContext:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: The query to search for
            filter_metadata: Optional metadata filter
            
        Returns:
            RAGContext with retrieved documents
        """
        # Search vector store
        results = self.vector_store.search(
            query, 
            top_k=self.top_k_documents,
            filter_metadata=filter_metadata
        )
        
        # Build context text
        context_parts = []
        total_chars = 0
        max_chars = int(self.max_context_tokens / self.tokens_per_char)
        
        for result in results:
            doc = result.document
            part = f"\n--- Document: {doc.id} ---\n{doc.content}\n"
            
            if total_chars + len(part) > max_chars:
                # Truncate to fit
                remaining = max_chars - total_chars
                if remaining > 100:  # Only add if meaningful
                    part = part[:remaining] + "..."
                    context_parts.append(part)
                break
            
            context_parts.append(part)
            total_chars += len(part)
        
        context_text = "\n".join(context_parts)
        estimated_tokens = int(total_chars * self.tokens_per_char)
        
        return RAGContext(
            query=query,
            documents=results,
            context_text=context_text,
            total_tokens=estimated_tokens
        )
    
    def query(self, question: str, 
              system_prompt: Optional[str] = None,
              filter_metadata: Optional[Dict[str, Any]] = None) -> RAGResponse:
        """
        Query the RAG system.
        
        Args:
            question: The question to answer
            system_prompt: Optional custom system prompt
            filter_metadata: Optional metadata filter for retrieval
            
        Returns:
            RAGResponse with answer and sources
        """
        import time
        start_time = time.time()
        
        # Retrieve context
        context = self.retrieve_context(question, filter_metadata)
        
        # Build prompt
        if system_prompt is None:
            system_prompt = """You are a helpful AI assistant. Use the provided context to answer the user's question. 
If the context doesn't contain relevant information, say so. Always cite your sources."""
        
        user_prompt = f"""Context:
{context.context_text}

Question: {question}

Please answer the question based on the context provided. Cite the relevant documents."""
        
        # Generate response
        response = self.model_router.generate(user_prompt, system=system_prompt)
        
        latency = (time.time() - start_time) * 1000
        
        # Build sources
        sources = [
            {
                "id": r.document.id,
                "score": r.score,
                "metadata": r.document.metadata
            }
            for r in context.documents
        ]
        
        return RAGResponse(
            answer=response.content,
            context=context,
            sources=sources,
            model_used=response.model,
            latency_ms=latency
        )
    
    def query_with_sources(self, question: str,
                          min_score: float = 0.5) -> Dict[str, Any]:
        """
        Query with detailed source information.
        
        Args:
            question: The question
            min_score: Minimum relevance score for sources
            
        Returns:
            Dict with answer, sources, and metadata
        """
        response = self.query(question)
        
        # Filter sources by score
        filtered_sources = [
            s for s in response.sources 
            if s['score'] >= min_score
        ]
        
        return {
            "answer": response.answer,
            "sources": filtered_sources,
            "model": response.model_used,
            "context_tokens": response.context.total_tokens,
            "latency_ms": response.latency_ms
        }
    
    def summarize_document(self, doc_id: str, 
                          max_length: str = "3 paragraphs") -> str:
        """
        Summarize a document.
        
        Args:
            doc_id: Document ID
            max_length: Desired summary length
            
        Returns:
            Summary text
        """
        doc = self.vector_store.get_document(doc_id)
        if not doc:
            raise ValueError(f"Document not found: {doc_id}")
        
        prompt = f"""Please summarize the following document in {max_length}:

{doc.content}

Summary:"""
        
        response = self.model_router.generate(prompt)
        return response.content
    
    def answer_from_documents(self, question: str, 
                             doc_ids: List[str]) -> RAGResponse:
        """
        Answer a question using specific documents.
        
        Args:
            question: The question
            doc_ids: List of document IDs to use
            
        Returns:
            RAGResponse
        """
        # Retrieve specific documents
        documents = []
        for doc_id in doc_ids:
            doc = self.vector_store.get_document(doc_id)
            if doc:
                documents.append(SearchResult(
                    document=doc,
                    score=1.0,
                    rank=len(documents) + 1
                ))
        
        # Build context
        context_parts = []
        for result in documents:
            doc = result.document
            context_parts.append(f"\n--- Document: {doc.id} ---\n{doc.content}\n")
        
        context_text = "\n".join(context_parts)
        
        context = RAGContext(
            query=question,
            documents=documents,
            context_text=context_text,
            total_tokens=int(len(context_text) * self.tokens_per_char)
        )
        
        # Generate answer
        prompt = f"""Context:
{context_text}

Question: {question}

Answer:"""
        
        response = self.model_router.generate(prompt)
        
        return RAGResponse(
            answer=response.content,
            context=context,
            sources=[{"id": d.document.id, "score": d.score} for d in documents],
            model_used=response.model,
            latency_ms=0
        )


# Global RAG engine instance
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Get the global RAG engine instance."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine


def set_rag_engine(engine: RAGEngine):
    """Set the global RAG engine instance."""
    global _rag_engine
    _rag_engine = engine