"""
Researcher + Writer UI - Project 3.1
Streamlit interface showing the multi-agent pipeline.
"""

import streamlit as st
import time
from dataclasses import asdict

from orchestrator import run_researcher, run_writer, ResearchNotes, ArticleDraft


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="Researcher + Writer",
    page_icon="✍️",
    layout="wide"
)

st.title("✍️ Researcher + Writer Pipeline")
st.markdown("*Your first multi-agent system: A2A handoff in action*")

# Initialize session state
if "research_notes" not in st.session_state:
    st.session_state.research_notes = None
if "article" not in st.session_state:
    st.session_state.article = None
if "stage" not in st.session_state:
    st.session_state.stage = "input"  # input, researching, writing, complete
if "metadata" not in st.session_state:
    st.session_state.metadata = {}

# Pipeline visualization
st.markdown("### Pipeline")

col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])

with col1:
    stage = st.session_state.stage
    if stage == "input":
        st.info("📝 **User Query**\nWaiting for input...")
    else:
        st.success("📝 **User Query**\n✓ Submitted")

with col2:
    st.markdown("<div style='text-align: center; padding-top: 20px;'>→</div>", unsafe_allow_html=True)

with col3:
    if stage in ["input"]:
        st.warning("🔍 **Researcher**\nIdle")
    elif stage == "researching":
        st.info("🔍 **Researcher**\n⏳ Working...")
    else:
        st.success("🔍 **Researcher**\n✓ Complete")

with col4:
    st.markdown("<div style='text-align: center; padding-top: 20px;'>→</div>", unsafe_allow_html=True)

with col5:
    if stage in ["input", "researching"]:
        st.warning("✍️ **Writer**\nIdle")
    elif stage == "writing":
        st.info("✍️ **Writer**\n⏳ Working...")
    else:
        st.success("✍️ **Writer**\n✓ Complete")

st.divider()

# Input section
if st.session_state.stage == "input":
    st.markdown("### What would you like an article about?")
    
    query = st.text_area(
        "Topic or Query",
        placeholder="e.g., 'The impact of AI on healthcare in 2026' or 'How remote work is changing company culture'",
        height=100
    )
    
    context = st.text_input(
        "Additional Context (optional)",
        placeholder="e.g., 'Focus on small businesses' or 'Make it beginner-friendly'"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚀 Start Pipeline", type="primary", disabled=not query):
            st.session_state.query = query
            st.session_state.context = context
            st.session_state.stage = "researching"
            st.rerun()

# Research stage
elif st.session_state.stage == "researching":
    st.markdown("### 🔍 Researcher Agent Working...")
    
    with st.spinner("Gathering information, extracting facts, and organizing research..."):
        start_time = time.time()
        research_notes, metadata = run_researcher(
            st.session_state.query,
            st.session_state.context
        )
        elapsed = time.time() - start_time
    
    st.session_state.research_notes = research_notes
    st.session_state.metadata["researcher"] = {**metadata, "elapsed_seconds": round(elapsed, 2)}
    st.session_state.stage = "writing"
    st.rerun()

# Writing stage
elif st.session_state.stage == "writing":
    st.markdown("### ✍️ Writer Agent Working...")
    
    # Show research notes while writing
    with st.expander("📋 Research Notes (Handoff Data)", expanded=True):
        notes = st.session_state.research_notes
        st.markdown(f"**Topic:** {notes.topic}")
        st.markdown(f"**Summary:** {notes.summary}")
        st.markdown("**Key Facts:**")
        for fact in notes.key_facts:
            st.markdown(f"- {fact}")
    
    with st.spinner("Creating outline, drafting, and polishing article..."):
        start_time = time.time()
        article, metadata = run_writer(st.session_state.research_notes)
        elapsed = time.time() - start_time
    
    st.session_state.article = article
    st.session_state.metadata["writer"] = {**metadata, "elapsed_seconds": round(elapsed, 2)}
    st.session_state.stage = "complete"
    st.rerun()

# Complete - show results
elif st.session_state.stage == "complete":
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Final Article", "🔍 Research Notes", "📊 Handoff Data", "📈 Metrics"])
    
    with tab1:
        article = st.session_state.article
        
        st.markdown(f"# {article.title}")
        st.divider()
        st.markdown(article.final_article)
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Word Count", article.word_count)
        with col2:
            st.download_button(
                "📥 Download Article",
                article.final_article,
                file_name=f"{article.title.replace(' ', '_')}.md",
                mime="text/markdown"
            )
    
    with tab2:
        notes = st.session_state.research_notes
        
        st.markdown(f"### {notes.topic}")
        st.markdown(f"**Summary:** {notes.summary}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Key Facts")
            for fact in notes.key_facts:
                st.markdown(f"✓ {fact}")
        
        with col2:
            st.markdown("#### Suggested Structure")
            for i, section in enumerate(notes.suggested_sections, 1):
                st.markdown(f"{i}. {section}")
        
        st.markdown("---")
        
        st.markdown(f"**Target Audience:** {notes.target_audience}")
        st.markdown(f"**Tone:** {notes.tone}")
        
        if notes.sources:
            st.markdown("#### Sources")
            for source in notes.sources:
                st.markdown(f"- **{source.get('title', 'Unknown')}**: {source.get('snippet', '')}")
    
    with tab3:
        st.markdown("### A2A Handoff Protocol")
        st.markdown("This is the structured JSON passed from Researcher → Writer:")
        
        st.code(st.session_state.research_notes.to_json(), language="json")
        
        st.markdown("""
        #### How Handoffs Work
        
        1. **Researcher Agent** outputs structured JSON
        2. **Orchestrator** validates the schema
        3. **Writer Agent** receives formatted research notes
        4. Each agent has a specialized system prompt
        
        This is the foundation of multi-agent systems!
        """)
    
    with tab4:
        st.markdown("### Pipeline Metrics")
        
        meta = st.session_state.metadata
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Researcher Agent")
            if "researcher" in meta:
                st.metric("Input Tokens", meta["researcher"]["input_tokens"])
                st.metric("Output Tokens", meta["researcher"]["output_tokens"])
                st.metric("Time", f"{meta['researcher']['elapsed_seconds']}s")
        
        with col2:
            st.markdown("#### Writer Agent")
            if "writer" in meta:
                st.metric("Input Tokens", meta["writer"]["input_tokens"])
                st.metric("Output Tokens", meta["writer"]["output_tokens"])
                st.metric("Time", f"{meta['writer']['elapsed_seconds']}s")
        
        with col3:
            st.markdown("#### Total")
            total_in = meta.get("researcher", {}).get("input_tokens", 0) + meta.get("writer", {}).get("input_tokens", 0)
            total_out = meta.get("researcher", {}).get("output_tokens", 0) + meta.get("writer", {}).get("output_tokens", 0)
            total_time = meta.get("researcher", {}).get("elapsed_seconds", 0) + meta.get("writer", {}).get("elapsed_seconds", 0)
            
            st.metric("Total Input Tokens", total_in)
            st.metric("Total Output Tokens", total_out)
            st.metric("Total Time", f"{total_time:.1f}s")
            
            # Cost estimate
            cost = (total_in * 0.000003) + (total_out * 0.000015)
            st.metric("Est. Cost", f"${cost:.4f}")
    
    # Reset button
    st.divider()
    if st.button("🔄 Start New Article", type="primary"):
        st.session_state.research_notes = None
        st.session_state.article = None
        st.session_state.stage = "input"
        st.session_state.metadata = {}
        st.rerun()

# Sidebar - Pipeline Info
with st.sidebar:
    st.header("📖 How It Works")
    
    st.markdown("""
    ### The Pipeline
    
    ```
    Query
      ↓
    🔍 Researcher Agent
      │ - Gathers info
      │ - Extracts facts
      │ - Suggests structure
      ↓
    📋 Handoff (JSON)
      ↓
    ✍️ Writer Agent
      │ - Creates outline
      │ - Writes draft
      │ - Polishes final
      ↓
    📄 Final Article
    ```
    
    ### What's Happening
    
    **Agent 1 (Researcher):**
    - Has a "researcher" system prompt
    - Outputs structured JSON
    - Focuses on facts & sources
    
    **Agent 2 (Writer):**
    - Has a "writer" system prompt
    - Receives research notes
    - Focuses on prose & polish
    
    ### Key Concept: Handoff
    
    The magic is the **structured handoff**:
    - Researcher outputs JSON
    - Writer receives formatted notes
    - Each agent is specialized
    """)
    
    st.divider()
    
    st.caption("Project 3.1 | learn-agentic-stack")
