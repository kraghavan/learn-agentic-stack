"""
Memory Client
Handles vector storage and retrieval using ChromaDB.
"""

import os
import hashlib
from datetime import datetime
from typing import Optional

import chromadb
from chromadb.config import Settings


# ChromaDB connection settings
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# Collection names
CONVERSATION_COLLECTION = "conversations"
FACTS_COLLECTION = "facts"


class MemoryClient:
    """Client for managing agent memory using ChromaDB."""
    
    def __init__(self):
        self.client = None
        self.conversations = None
        self.facts = None
        self._connect()
    
    def _connect(self):
        """Connect to ChromaDB server with retry logic."""
        import time
        
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.client = chromadb.HttpClient(
                    host=CHROMA_HOST,
                    port=CHROMA_PORT,
                )
                
                # Test connection
                self.client.heartbeat()
                
                # Get or create collections
                self.conversations = self.client.get_or_create_collection(
                    name=CONVERSATION_COLLECTION,
                    metadata={"description": "Conversation history with embeddings"}
                )
                
                self.facts = self.client.get_or_create_collection(
                    name=FACTS_COLLECTION,
                    metadata={"description": "Extracted facts and knowledge"}
                )
                
                return  # Success!
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"ChromaDB not ready, retrying in {retry_delay}s... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    raise ConnectionError(f"Failed to connect to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT} after {max_retries} attempts: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to ChromaDB."""
        try:
            self.client.heartbeat()
            return True
        except:
            return False
    
    def _generate_id(self, text: str) -> str:
        """Generate a unique ID for a piece of text."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{text}{timestamp}".encode()).hexdigest()[:16]
    
    # ============== Conversation Memory ==============
    
    def store_message(
        self,
        role: str,
        content: str,
        session_id: str = "default",
        metadata: dict = None
    ) -> str:
        """
        Store a conversation message.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            session_id: Conversation session ID
            metadata: Additional metadata
        
        Returns:
            Message ID
        """
        msg_id = self._generate_id(content)
        
        msg_metadata = {
            "role": role,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }
        
        if metadata:
            msg_metadata.update(metadata)
        
        self.conversations.add(
            ids=[msg_id],
            documents=[content],
            metadatas=[msg_metadata]
        )
        
        return msg_id
    
    def get_relevant_history(
        self,
        query: str,
        session_id: str = None,
        n_results: int = 5,
        include_all_sessions: bool = False
    ) -> list[dict]:
        """
        Retrieve relevant conversation history.
        
        Args:
            query: Query to find relevant messages
            session_id: Filter by session (optional)
            n_results: Number of results to return
            include_all_sessions: Search across all sessions
        
        Returns:
            List of relevant messages with metadata
        """
        where_filter = None
        if session_id and not include_all_sessions:
            where_filter = {"session_id": session_id}
        
        try:
            results = self.conversations.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            messages = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    messages.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "relevance": 1 - results['distances'][0][i] if results['distances'] else 0,
                    })
            
            return messages
        
        except Exception as e:
            print(f"Error querying conversations: {e}")
            return []
    
    def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> list[dict]:
        """Get full conversation history for a session."""
        try:
            results = self.conversations.get(
                where={"session_id": session_id},
                include=["documents", "metadatas"]
            )
            
            messages = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    messages.append({
                        "content": doc,
                        "metadata": results['metadatas'][i] if results['metadatas'] else {},
                    })
            
            # Sort by timestamp
            messages.sort(key=lambda x: x['metadata'].get('timestamp', ''))
            
            return messages[-limit:]
        
        except Exception as e:
            print(f"Error getting session history: {e}")
            return []
    
    # ============== Facts Memory ==============
    
    def store_fact(
        self,
        fact: str,
        category: str = "general",
        source: str = None,
        confidence: float = 1.0
    ) -> str:
        """
        Store a fact or piece of knowledge.
        
        Args:
            fact: The fact to store
            category: Category (e.g., 'user_preference', 'general', 'task')
            source: Where the fact came from
            confidence: Confidence score (0-1)
        
        Returns:
            Fact ID
        """
        fact_id = self._generate_id(fact)
        
        metadata = {
            "category": category,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }
        
        if source:
            metadata["source"] = source
        
        self.facts.add(
            ids=[fact_id],
            documents=[fact],
            metadatas=[metadata]
        )
        
        return fact_id
    
    def get_relevant_facts(
        self,
        query: str,
        category: str = None,
        n_results: int = 5
    ) -> list[dict]:
        """
        Retrieve relevant facts.
        
        Args:
            query: Query to find relevant facts
            category: Filter by category (optional)
            n_results: Number of results
        
        Returns:
            List of relevant facts
        """
        where_filter = None
        if category:
            where_filter = {"category": category}
        
        try:
            results = self.facts.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            facts = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    facts.append({
                        "fact": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "relevance": 1 - results['distances'][0][i] if results['distances'] else 0,
                    })
            
            return facts
        
        except Exception as e:
            print(f"Error querying facts: {e}")
            return []
    
    def get_all_facts(self, category: str = None) -> list[dict]:
        """Get all stored facts."""
        try:
            if category:
                results = self.facts.get(
                    where={"category": category},
                    include=["documents", "metadatas"]
                )
            else:
                results = self.facts.get(include=["documents", "metadatas"])
            
            facts = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    facts.append({
                        "fact": doc,
                        "metadata": results['metadatas'][i] if results['metadatas'] else {},
                    })
            
            return facts
        
        except Exception as e:
            print(f"Error getting facts: {e}")
            return []
    
    # ============== Memory Management ==============
    
    def forget_session(self, session_id: str) -> bool:
        """Delete all messages from a session."""
        try:
            # Get IDs first
            results = self.conversations.get(
                where={"session_id": session_id},
                include=[]
            )
            
            if results and results['ids']:
                self.conversations.delete(ids=results['ids'])
                return True
            return False
        
        except Exception as e:
            print(f"Error forgetting session: {e}")
            return False
    
    def forget_fact(self, fact_id: str) -> bool:
        """Delete a specific fact."""
        try:
            self.facts.delete(ids=[fact_id])
            return True
        except Exception as e:
            print(f"Error forgetting fact: {e}")
            return False
    
    def clear_all_memory(self) -> bool:
        """Clear all memory (use with caution!)."""
        try:
            # Delete and recreate collections
            self.client.delete_collection(CONVERSATION_COLLECTION)
            self.client.delete_collection(FACTS_COLLECTION)
            
            self.conversations = self.client.get_or_create_collection(
                name=CONVERSATION_COLLECTION,
                metadata={"description": "Conversation history with embeddings"}
            )
            
            self.facts = self.client.get_or_create_collection(
                name=FACTS_COLLECTION,
                metadata={"description": "Extracted facts and knowledge"}
            )
            
            return True
        
        except Exception as e:
            print(f"Error clearing memory: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get memory statistics."""
        try:
            return {
                "conversations_count": self.conversations.count(),
                "facts_count": self.facts.count(),
                "connected": self.is_connected(),
            }
        except:
            return {
                "conversations_count": 0,
                "facts_count": 0,
                "connected": False,
            }


# Singleton instance
_client = None

def get_memory_client() -> MemoryClient:
    """Get or create the memory client singleton."""
    global _client
    if _client is None:
        _client = MemoryClient()
    return _client


if __name__ == "__main__":
    # Test
    client = get_memory_client()
    print(f"Connected: {client.is_connected()}")
    print(f"Stats: {client.get_stats()}")
