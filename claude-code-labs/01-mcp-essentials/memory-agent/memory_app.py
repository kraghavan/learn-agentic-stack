"""
Memory Agent - Project 2.3
A conversational agent with persistent memory using ChromaDB.
"""

import os
import uuid
from datetime import datetime

import streamlit as st
from anthropic import Anthropic

from memory_client import get_memory_client, MemoryClient

# Initialize Claude
claude = Anthropic()


def extract_facts_from_conversation(user_message: str, assistant_response: str) -> list[str]:
    """Use Claude to extract memorable facts from the conversation."""
    
    prompt = f"""Analyze this conversation exchange and extract any facts worth remembering about the user.

User said: "{user_message}"
Assistant said: "{assistant_response}"

Extract facts like:
- User preferences (likes, dislikes)
- Personal information shared (name, job, location)
- Goals or tasks mentioned
- Important context for future conversations

Return a JSON array of fact strings. If no facts worth remembering, return [].
Example: ["User's name is Alice", "User prefers Python over JavaScript", "User is working on a web app"]

Return ONLY the JSON array, nothing else."""

    try:
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        result = response.content[0].text.strip()
        
        # Clean up response
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        return json.loads(result)
    
    except Exception as e:
        print(f"Error extracting facts: {e}")
        return []


def build_context_prompt(
    user_message: str,
    memory_client: MemoryClient,
    session_id: str
) -> str:
    """Build a context-aware system prompt with relevant memories."""
    
    # Get relevant past conversations
    relevant_history = memory_client.get_relevant_history(
        query=user_message,
        session_id=session_id,
        n_results=3,
        include_all_sessions=True
    )
    
    # Get relevant facts
    relevant_facts = memory_client.get_relevant_facts(
        query=user_message,
        n_results=5
    )
    
    # Build context section
    context_parts = []
    
    if relevant_facts:
        facts_text = "\n".join([f"- {f['fact']}" for f in relevant_facts])
        context_parts.append(f"## Known Facts About the User\n{facts_text}")
    
    if relevant_history:
        history_text = "\n".join([
            f"- [{h['metadata'].get('role', 'unknown')}] {h['content'][:200]}..."
            for h in relevant_history
        ])
        context_parts.append(f"## Relevant Past Conversations\n{history_text}")
    
    context = "\n\n".join(context_parts) if context_parts else "No relevant memories found."
    
    system_prompt = f"""You are a helpful AI assistant with memory. You remember past conversations and facts about the user.

## Your Memory
{context}

## Instructions
1. Use your memory to provide personalized, contextual responses
2. Reference past conversations when relevant (e.g., "As you mentioned before...")
3. Remember user preferences and facts
4. Be natural - don't force memory references if not relevant
5. If you remember something relevant, briefly acknowledge it

Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""
    
    return system_prompt, relevant_history, relevant_facts


def chat_with_memory(
    user_message: str,
    memory_client: MemoryClient,
    session_id: str
) -> tuple[str, list, list]:
    """
    Chat with the memory-enabled agent.
    
    Returns:
        (response, relevant_history, relevant_facts)
    """
    
    # Build context-aware prompt
    system_prompt, relevant_history, relevant_facts = build_context_prompt(
        user_message, memory_client, session_id
    )
    
    # Get recent session messages for conversation continuity
    recent_messages = memory_client.get_session_history(session_id, limit=10)
    
    # Build messages list
    messages = []
    for msg in recent_messages[-6:]:  # Last 6 messages
        messages.append({
            "role": msg['metadata'].get('role', 'user'),
            "content": msg['content']
        })
    
    messages.append({"role": "user", "content": user_message})
    
    # Call Claude
    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system_prompt,
        messages=messages
    )
    
    assistant_response = response.content[0].text
    
    # Store messages in memory
    memory_client.store_message("user", user_message, session_id)
    memory_client.store_message("assistant", assistant_response, session_id)
    
    # Extract and store facts (async-ish, after response)
    facts = extract_facts_from_conversation(user_message, assistant_response)
    for fact in facts:
        memory_client.store_fact(
            fact=fact,
            category="user_info",
            source=f"session:{session_id}"
        )
    
    return assistant_response, relevant_history, relevant_facts


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="Memory Agent",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Memory Agent")
st.markdown("*An AI that remembers your conversations*")

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory_client" not in st.session_state:
    try:
        st.session_state.memory_client = get_memory_client()
    except ConnectionError as e:
        st.session_state.memory_client = None
        st.error(f"Could not connect to ChromaDB: {e}")

# Sidebar
with st.sidebar:
    st.header("🧠 Memory Status")
    
    memory_client = st.session_state.memory_client
    
    if memory_client and memory_client.is_connected():
        st.success("✓ Connected to ChromaDB")
        
        stats = memory_client.get_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Conversations", stats['conversations_count'])
        with col2:
            st.metric("Facts", stats['facts_count'])
    else:
        st.error("✗ Not connected to ChromaDB")
        st.info("Make sure ChromaDB is running:\n`docker-compose up -d`")
    
    st.divider()
    
    # Session management
    st.subheader("📝 Session")
    st.caption(f"ID: `{st.session_state.session_id}`")
    
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Memory viewer
    st.subheader("💾 Stored Facts")
    
    if memory_client:
        facts = memory_client.get_all_facts()
        
        if facts:
            for i, fact in enumerate(facts[:10]):
                with st.expander(fact['fact'][:40] + "...", expanded=False):
                    st.write(fact['fact'])
                    st.caption(f"Category: {fact['metadata'].get('category', 'unknown')}")
                    if st.button("🗑️ Forget", key=f"forget_{i}"):
                        # Note: Would need fact ID to delete
                        st.info("Delete functionality requires fact ID tracking")
        else:
            st.caption("No facts stored yet")
    
    st.divider()
    
    # Memory management
    st.subheader("⚙️ Memory Management")
    
    if st.button("🗑️ Clear Current Session", use_container_width=True):
        if memory_client:
            memory_client.forget_session(st.session_state.session_id)
            st.session_state.messages = []
            st.success("Session cleared!")
            st.rerun()
    
    if st.button("⚠️ Clear ALL Memory", use_container_width=True, type="secondary"):
        if memory_client:
            if st.session_state.get("confirm_clear"):
                memory_client.clear_all_memory()
                st.session_state.messages = []
                st.session_state.confirm_clear = False
                st.success("All memory cleared!")
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm!")

# Main chat interface
if not st.session_state.memory_client or not st.session_state.memory_client.is_connected():
    st.warning("⚠️ ChromaDB is not connected. Start it with `docker-compose up -d`")
    
    st.markdown("""
    ### Quick Start
    
    ```bash
    cd memory-agent
    docker-compose up -d
    ```
    
    Then refresh this page.
    
    ### What This App Does
    
    - 💬 **Remembers conversations** - Past chats are stored and retrieved when relevant
    - 🧠 **Extracts facts** - Learns about you from conversations
    - 🔍 **Contextual responses** - Uses memory to give personalized answers
    - 🗑️ **Memory management** - Clear sessions or all memory
    """)

else:
    # Chat display
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
                # Show memory indicators
                if msg["role"] == "assistant" and msg.get("memories"):
                    with st.expander("🧠 Memory used", expanded=False):
                        if msg["memories"].get("facts"):
                            st.markdown("**Relevant facts:**")
                            for f in msg["memories"]["facts"]:
                                score = f.get('relevance', 0) * 100
                                st.markdown(f"- {f['fact']} ({score:.0f}% relevant)")
                        
                        if msg["memories"].get("history"):
                            st.markdown("**Past conversations:**")
                            for h in msg["memories"]["history"]:
                                score = h.get('relevance', 0) * 100
                                st.markdown(f"- {h['content'][:100]}... ({score:.0f}%)")
    
    # Chat input
    if prompt := st.chat_input("Say something..."):
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get response with memory
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, history, facts = chat_with_memory(
                    prompt,
                    st.session_state.memory_client,
                    st.session_state.session_id
                )
            
            st.write(response)
            
            # Show memory indicators
            if history or facts:
                with st.expander("🧠 Memory used", expanded=False):
                    if facts:
                        st.markdown("**Relevant facts:**")
                        for f in facts:
                            score = f.get('relevance', 0) * 100
                            st.markdown(f"- {f['fact']} ({score:.0f}% relevant)")
                    
                    if history:
                        st.markdown("**Past conversations:**")
                        for h in history:
                            score = h.get('relevance', 0) * 100
                            st.markdown(f"- {h['content'][:100]}... ({score:.0f}%)")
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "memories": {"facts": facts, "history": history}
        })

# Footer
st.divider()
st.caption("Project 2.3 - Memory Agent with ChromaDB | learn-agentic-stack")
