"""
RAG Chat - Project 4.1
Chat with your knowledge base using retrieval-augmented generation.
"""

import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from anthropic import Anthropic

from knowledge_base import KnowledgeBase, Citation


@dataclass
class ChatMessage:
    """A message in the chat history."""
    role: str  # "user" or "assistant"
    content: str
    citations: list[Citation] = field(default_factory=list)
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ChatResponse:
    """Response from the RAG chat."""
    content: str
    citations: list[Citation]
    context_used: str
    tokens_used: dict


class RAGChat:
    """
    Chat interface for the knowledge base.
    
    Uses RAG (Retrieval-Augmented Generation) to answer questions
    based on indexed documents with proper citations.
    """
    
    SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context from a personal knowledge base.

IMPORTANT RULES:
1. Answer ONLY based on the provided context
2. If the context doesn't contain relevant information, say so
3. Always cite your sources using [Source N] format
4. Be precise and accurate
5. If you're unsure, acknowledge uncertainty

When citing, use the exact source numbers from the context (e.g., "According to [Source 1]...").

If the user's question cannot be answered from the provided context, respond with:
"I don't have information about that in my knowledge base. The documents I have access to cover: [briefly list topics from context]."
"""
    
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        model: str = "claude-sonnet-4-20250514",
        max_context_tokens: int = 2000,
        n_results: int = 5
    ):
        """
        Initialize RAG chat.
        
        Args:
            knowledge_base: The knowledge base to query
            model: Claude model to use
            max_context_tokens: Max tokens for retrieved context
            n_results: Number of chunks to retrieve
        """
        self.kb = knowledge_base
        self.model = model
        self.max_context_tokens = max_context_tokens
        self.n_results = n_results
        
        self.client = Anthropic()
        self.history: list[ChatMessage] = []
    
    def chat(
        self,
        query: str,
        include_history: bool = True,
        search_filter: dict = None
    ) -> ChatResponse:
        """
        Send a message and get a response.
        
        Args:
            query: User's question
            include_history: Whether to include conversation history
            search_filter: Optional filters for document search
        
        Returns:
            ChatResponse with answer and citations
        """
        # Retrieve relevant context
        context, citations = self.kb.get_context_for_query(
            query,
            n_results=self.n_results,
            max_tokens=self.max_context_tokens
        )
        
        # Build the prompt
        if context:
            user_message = f"""## Retrieved Context

{context}

---

## User Question

{query}

Please answer the question based on the context above. Cite sources using [Source N] format."""
        else:
            user_message = f"""## Note
No relevant documents were found in the knowledge base.

## User Question
{query}

Please let the user know that no relevant information was found."""
        
        # Build messages
        messages = []
        
        if include_history and self.history:
            # Include recent history (last 5 exchanges)
            recent_history = self.history[-10:]
            for msg in recent_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=self.SYSTEM_PROMPT,
            messages=messages
        )
        
        assistant_content = response.content[0].text
        
        # Store in history
        self.history.append(ChatMessage(
            role="user",
            content=query
        ))
        self.history.append(ChatMessage(
            role="assistant",
            content=assistant_content,
            citations=citations
        ))
        
        return ChatResponse(
            content=assistant_content,
            citations=citations,
            context_used=context,
            tokens_used={
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens
            }
        )
    
    def ask(self, query: str) -> str:
        """Simple interface - just returns the answer."""
        response = self.chat(query)
        return response.content
    
    def ask_with_citations(self, query: str) -> tuple[str, list[str]]:
        """Returns answer and formatted citations."""
        response = self.chat(query)
        formatted_citations = [c.format() for c in response.citations]
        return response.content, formatted_citations
    
    def clear_history(self):
        """Clear conversation history."""
        self.history = []
    
    def get_history(self) -> list[ChatMessage]:
        """Get conversation history."""
        return self.history
    
    def search_only(self, query: str, n_results: int = 5) -> list[dict]:
        """
        Search without generating a response.
        Useful for exploring what's in the knowledge base.
        """
        results = self.kb.search(query, n_results=n_results)
        
        return [{
            "document": r.chunk.document_name,
            "content": r.chunk.content,
            "score": round(r.score, 3),
            "chunk_index": r.chunk.chunk_index
        } for r in results]


class MultiDocumentChat(RAGChat):
    """
    Enhanced RAG chat that can compare across documents.
    """
    
    COMPARISON_PROMPT = """You are an assistant that can compare and synthesize information from multiple documents.

When comparing documents:
1. Identify similarities and differences
2. Note agreements and contradictions
3. Cite specific sources for each claim
4. Provide a balanced synthesis

Always cite using [Source N] format."""
    
    def compare(self, topic: str, document_ids: list[str] = None) -> ChatResponse:
        """
        Compare how different documents discuss a topic.
        
        Args:
            topic: The topic to compare
            document_ids: Specific documents to compare (optional)
        """
        # Get context from specified documents or all
        context, citations = self.kb.get_context_for_query(
            topic,
            n_results=self.n_results * 2,  # Get more for comparison
            max_tokens=self.max_context_tokens
        )
        
        # Build comparison prompt
        user_message = f"""## Documents to Compare

{context}

---

## Comparison Request

Please compare how these documents discuss: {topic}

Identify:
1. Key similarities
2. Notable differences
3. Unique perspectives from each source
4. Overall synthesis

Cite each point with [Source N]."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=self.COMPARISON_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        
        return ChatResponse(
            content=response.content[0].text,
            citations=citations,
            context_used=context,
            tokens_used={
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens
            }
        )
    
    def summarize_document(self, document_id: str) -> str:
        """Generate a summary of a specific document."""
        chunks = self.kb.get_document_chunks(document_id)
        
        if not chunks:
            return "Document not found."
        
        # Combine chunks
        full_content = "\n\n".join([c.content for c in chunks])
        
        # Truncate if too long
        if len(full_content) > 8000:
            full_content = full_content[:8000] + "\n\n[... content truncated ...]"
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system="Summarize the following document concisely, capturing the main points.",
            messages=[{"role": "user", "content": full_content}]
        )
        
        return response.content[0].text


if __name__ == "__main__":
    from document_processor import DocumentProcessor, DocumentType
    from knowledge_base import KnowledgeBase
    
    # Test
    kb = KnowledgeBase(persist_directory="./test_kb")
    
    # Add some test documents
    processor = DocumentProcessor()
    
    doc1 = processor.process_text("""
    # Python Best Practices
    
    Python is a versatile programming language. Here are some best practices:
    
    ## Code Style
    - Follow PEP 8 guidelines
    - Use meaningful variable names
    - Keep functions small and focused
    
    ## Testing
    - Write unit tests for all functions
    - Use pytest for testing
    - Aim for high test coverage
    """, "python_guide.md", DocumentType.MARKDOWN)
    
    doc2 = processor.process_text("""
    # JavaScript Best Practices
    
    JavaScript is essential for web development. Key practices include:
    
    ## Code Style
    - Use ESLint for linting
    - Prefer const over let
    - Use arrow functions where appropriate
    
    ## Testing
    - Write tests with Jest
    - Test components in isolation
    - Use React Testing Library for UI
    """, "javascript_guide.md", DocumentType.MARKDOWN)
    
    kb.add_document(doc1)
    kb.add_document(doc2)
    
    # Test RAG chat
    chat = RAGChat(kb)
    
    print("=== Basic Question ===")
    response = chat.chat("What are Python testing best practices?")
    print(f"Answer: {response.content}")
    print(f"Citations: {[c.format() for c in response.citations]}")
    
    print("\n=== Comparison ===")
    multi_chat = MultiDocumentChat(kb)
    response = multi_chat.compare("code style guidelines")
    print(f"Comparison: {response.content}")
    
    # Cleanup
    kb.clear()
