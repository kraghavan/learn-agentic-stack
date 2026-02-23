"""
Knowledge Base - Project 4.1
ChromaDB-powered vector storage with semantic search.
"""

import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

import chromadb
from chromadb.config import Settings

from document_processor import Document, DocumentChunk, DocumentType


@dataclass
class SearchResult:
    """A search result with relevance score."""
    chunk: DocumentChunk
    score: float
    rank: int
    
    def to_dict(self) -> dict:
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "rank": self.rank
        }


@dataclass
class Citation:
    """A citation for RAG responses."""
    document_name: str
    document_id: str
    chunk_index: int
    content_preview: str
    relevance_score: float
    
    def format(self) -> str:
        """Format citation for display."""
        return f"[{self.document_name}, chunk {self.chunk_index + 1}]"


class KnowledgeBase:
    """
    Personal knowledge base with vector search.
    
    Features:
    - Document storage and retrieval
    - Semantic search with embeddings
    - Metadata filtering
    - Citation tracking
    """
    
    def __init__(
        self,
        persist_directory: str = "./kb_data",
        collection_name: str = "knowledge_base"
    ):
        """
        Initialize the knowledge base.
        
        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the ChromaDB collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Personal knowledge base"}
        )
        
        # Document metadata store
        self._load_document_index()
    
    def _load_document_index(self):
        """Load document index from file."""
        index_path = os.path.join(self.persist_directory, "document_index.json")
        
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                self.document_index = json.load(f)
        else:
            self.document_index = {}
    
    def _save_document_index(self):
        """Save document index to file."""
        os.makedirs(self.persist_directory, exist_ok=True)
        index_path = os.path.join(self.persist_directory, "document_index.json")
        
        with open(index_path, "w") as f:
            json.dump(self.document_index, f, indent=2)
    
    def add_document(self, document: Document) -> dict:
        """
        Add a document to the knowledge base.
        
        Args:
            document: Processed document with chunks
        
        Returns:
            Summary of the operation
        """
        if not document.chunks:
            raise ValueError("Document has no chunks")
        
        # Check if document already exists
        if document.id in self.document_index:
            # Remove old version first
            self.remove_document(document.id)
        
        # Prepare data for ChromaDB
        ids = [chunk.id for chunk in document.chunks]
        documents = [chunk.content for chunk in document.chunks]
        metadatas = [chunk.to_dict() for chunk in document.chunks]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        # Update document index
        self.document_index[document.id] = {
            "name": document.name,
            "path": document.path,
            "type": document.doc_type.value,
            "chunk_count": len(document.chunks),
            "content_length": len(document.content),
            "created_at": document.created_at,
            "indexed_at": datetime.now().isoformat(),
            "metadata": document.metadata
        }
        
        self._save_document_index()
        
        return {
            "document_id": document.id,
            "name": document.name,
            "chunks_added": len(document.chunks),
            "status": "success"
        }
    
    def remove_document(self, document_id: str) -> bool:
        """Remove a document and all its chunks."""
        if document_id not in self.document_index:
            return False
        
        # Get chunk IDs for this document
        doc_info = self.document_index[document_id]
        chunk_ids = [f"{document_id}_{i}" for i in range(doc_info["chunk_count"])]
        
        # Remove from collection
        try:
            self.collection.delete(ids=chunk_ids)
        except Exception:
            pass  # Chunks may not exist
        
        # Remove from index
        del self.document_index[document_id]
        self._save_document_index()
        
        return True
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        document_types: list[DocumentType] = None,
        document_ids: list[str] = None,
        min_score: float = 0.0
    ) -> list[SearchResult]:
        """
        Semantic search across the knowledge base.
        
        Args:
            query: Search query
            n_results: Maximum number of results
            document_types: Filter by document types
            document_ids: Filter by specific documents
            min_score: Minimum relevance score (0-1)
        
        Returns:
            List of SearchResult objects
        """
        # Build where clause for filtering
        where = None
        where_conditions = []
        
        if document_types:
            type_values = [dt.value for dt in document_types]
            if len(type_values) == 1:
                where_conditions.append({"document_type": type_values[0]})
            else:
                where_conditions.append({"document_type": {"$in": type_values}})
        
        if document_ids:
            if len(document_ids) == 1:
                where_conditions.append({"document_id": document_ids[0]})
            else:
                where_conditions.append({"document_id": {"$in": document_ids}})
        
        if len(where_conditions) == 1:
            where = where_conditions[0]
        elif len(where_conditions) > 1:
            where = {"$and": where_conditions}
        
        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        
        if results["ids"] and results["ids"][0]:
            for i, (chunk_id, content, metadata, distance) in enumerate(zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # Convert distance to similarity score (ChromaDB returns L2 distance)
                # Lower distance = higher similarity
                score = 1 / (1 + distance)
                
                if score < min_score:
                    continue
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=content,
                    document_id=metadata.get("document_id", ""),
                    document_name=metadata.get("document_name", ""),
                    document_type=DocumentType(metadata.get("document_type", "text")),
                    chunk_index=metadata.get("chunk_index", 0),
                    total_chunks=metadata.get("total_chunks", 1),
                    start_char=metadata.get("start_char", 0),
                    end_char=metadata.get("end_char", 0),
                    metadata={k: v for k, v in metadata.items() if k not in [
                        "id", "content", "document_id", "document_name",
                        "document_type", "chunk_index", "total_chunks",
                        "start_char", "end_char"
                    ]}
                )
                
                search_results.append(SearchResult(
                    chunk=chunk,
                    score=score,
                    rank=i + 1
                ))
        
        return search_results
    
    def get_context_for_query(
        self,
        query: str,
        n_results: int = 5,
        max_tokens: int = 2000
    ) -> tuple[str, list[Citation]]:
        """
        Get relevant context for a RAG query.
        
        Args:
            query: The user's question
            n_results: Number of chunks to retrieve
            max_tokens: Approximate max tokens for context
        
        Returns:
            (context_string, list_of_citations)
        """
        results = self.search(query, n_results=n_results)
        
        context_parts = []
        citations = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough token-to-char conversion
        
        for result in results:
            chunk = result.chunk
            
            # Check if we have room
            if total_chars + len(chunk.content) > max_chars:
                # Truncate if needed
                remaining = max_chars - total_chars
                if remaining > 100:
                    content = chunk.content[:remaining] + "..."
                else:
                    break
            else:
                content = chunk.content
            
            # Add to context
            citation_num = len(citations) + 1
            context_parts.append(f"[Source {citation_num}: {chunk.document_name}]\n{content}")
            
            # Track citation
            citations.append(Citation(
                document_name=chunk.document_name,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content_preview=chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content,
                relevance_score=result.score
            ))
            
            total_chars += len(content)
        
        context = "\n\n---\n\n".join(context_parts)
        
        return context, citations
    
    def get_document(self, document_id: str) -> Optional[dict]:
        """Get document metadata by ID."""
        return self.document_index.get(document_id)
    
    def list_documents(self) -> list[dict]:
        """List all documents in the knowledge base."""
        documents = []
        
        for doc_id, info in self.document_index.items():
            documents.append({
                "id": doc_id,
                **info
            })
        
        return sorted(documents, key=lambda x: x.get("indexed_at", ""), reverse=True)
    
    def get_stats(self) -> dict:
        """Get knowledge base statistics."""
        total_chunks = self.collection.count()
        total_docs = len(self.document_index)
        
        # Type breakdown
        type_counts = {}
        for info in self.document_index.values():
            doc_type = info.get("type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "document_types": type_counts,
            "storage_path": self.persist_directory
        }
    
    def clear(self):
        """Clear all data from the knowledge base."""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Personal knowledge base"}
        )
        
        # Clear document index
        self.document_index = {}
        self._save_document_index()
    
    def get_document_chunks(self, document_id: str) -> list[DocumentChunk]:
        """Get all chunks for a specific document."""
        doc_info = self.document_index.get(document_id)
        if not doc_info:
            return []
        
        chunk_ids = [f"{document_id}_{i}" for i in range(doc_info["chunk_count"])]
        
        results = self.collection.get(
            ids=chunk_ids,
            include=["documents", "metadatas"]
        )
        
        chunks = []
        if results["ids"]:
            for chunk_id, content, metadata in zip(
                results["ids"],
                results["documents"],
                results["metadatas"]
            ):
                chunks.append(DocumentChunk(
                    id=chunk_id,
                    content=content,
                    document_id=metadata.get("document_id", ""),
                    document_name=metadata.get("document_name", ""),
                    document_type=DocumentType(metadata.get("document_type", "text")),
                    chunk_index=metadata.get("chunk_index", 0),
                    total_chunks=metadata.get("total_chunks", 1),
                    start_char=metadata.get("start_char", 0),
                    end_char=metadata.get("end_char", 0)
                ))
        
        return sorted(chunks, key=lambda x: x.chunk_index)


if __name__ == "__main__":
    from document_processor import DocumentProcessor
    
    # Test
    kb = KnowledgeBase(persist_directory="./test_kb")
    
    # Create a test document
    processor = DocumentProcessor()
    doc = processor.process_text("""
    # Machine Learning Guide
    
    Machine learning is a subset of AI that enables computers to learn from data.
    
    ## Supervised Learning
    
    In supervised learning, we train models on labeled data. Common algorithms include:
    - Linear Regression
    - Decision Trees
    - Neural Networks
    
    ## Unsupervised Learning
    
    Unsupervised learning finds patterns in unlabeled data. Examples:
    - K-Means Clustering
    - PCA
    - Autoencoders
    """, "ml_guide.md", DocumentType.MARKDOWN)
    
    # Add to knowledge base
    result = kb.add_document(doc)
    print(f"Added document: {result}")
    
    # Search
    results = kb.search("what is supervised learning?")
    print(f"\nSearch results: {len(results)}")
    for r in results:
        print(f"  [{r.score:.3f}] {r.chunk.document_name}: {r.chunk.content[:100]}...")
    
    # Get context with citations
    context, citations = kb.get_context_for_query("explain neural networks")
    print(f"\nContext length: {len(context)} chars")
    print(f"Citations: {[c.format() for c in citations]}")
    
    # Stats
    print(f"\nStats: {kb.get_stats()}")
    
    # Cleanup
    kb.clear()
