"""
Personal Knowledge Base UI - Project 4.1
Full-featured Streamlit interface for knowledge management.
"""

import os
import tempfile
import streamlit as st
from pathlib import Path

from document_processor import DocumentProcessor, DocumentType
from knowledge_base import KnowledgeBase
from rag_chat import RAGChat, MultiDocumentChat
from knowledge_graph import KnowledgeGraphExtractor, DocumentSimilarityGraph


# ============== PAGE CONFIG ==============

st.set_page_config(
    page_title="Personal Knowledge Base",
    page_icon="📚",
    layout="wide"
)

# ============== INITIALIZE ==============

@st.cache_resource
def get_knowledge_base():
    """Get or create the knowledge base."""
    kb_path = os.environ.get("KB_PATH", "./kb_data")
    return KnowledgeBase(persist_directory=kb_path)

@st.cache_resource
def get_document_processor():
    """Get document processor."""
    return DocumentProcessor(
        chunk_size=500,
        chunk_overlap=50
    )

# Initialize
kb = get_knowledge_base()
processor = get_document_processor()

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "rag_chat" not in st.session_state:
    st.session_state.rag_chat = RAGChat(kb)

# ============== SIDEBAR ==============

with st.sidebar:
    st.title("📚 Knowledge Base")
    
    # Stats
    stats = kb.get_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents", stats["total_documents"])
    with col2:
        st.metric("Chunks", stats["total_chunks"])
    
    st.divider()
    
    # Navigation
    page = st.radio(
        "Navigate",
        ["💬 Chat", "📤 Upload", "🔍 Search", "📄 Documents", "🕸️ Graph"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Quick actions
    st.markdown("### Quick Actions")
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.rag_chat.clear_history()
        st.rerun()
    
    if st.button("⚠️ Clear All Data", use_container_width=True):
        if st.session_state.get("confirm_clear"):
            kb.clear()
            st.session_state.chat_history = []
            st.session_state.confirm_clear = False
            st.rerun()
        else:
            st.session_state.confirm_clear = True
            st.warning("Click again to confirm")

# ============== MAIN CONTENT ==============

st.title("📚 Personal Knowledge Base")

# ============== CHAT PAGE ==============

if page == "💬 Chat":
    st.markdown("### Chat with your documents")
    
    if stats["total_documents"] == 0:
        st.info("📤 Upload some documents first to start chatting!")
    else:
        # Chat interface
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("citations"):
                    with st.expander("📎 Sources"):
                        for citation in msg["citations"]:
                            st.caption(f"• {citation}")
        
        # Chat input
        if prompt := st.chat_input("Ask a question about your documents..."):
            # Add user message
            st.session_state.chat_history.append({
                "role": "user",
                "content": prompt
            })
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get response
            with st.chat_message("assistant"):
                with st.spinner("Searching knowledge base..."):
                    response = st.session_state.rag_chat.chat(prompt)
                
                st.markdown(response.content)
                
                if response.citations:
                    with st.expander("📎 Sources"):
                        for citation in response.citations:
                            st.caption(f"• {citation.format()} (relevance: {citation.relevance_score:.2f})")
                
                # Add to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.content,
                    "citations": [c.format() for c in response.citations]
                })

# ============== UPLOAD PAGE ==============

elif page == "📤 Upload":
    st.markdown("### Upload Documents")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        type=["pdf", "md", "txt", "py", "js", "html", "json", "yaml", "yml"]
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.caption(f"Size: {uploaded_file.size:,} bytes")
                
                with col2:
                    if st.button("📥 Index", key=f"index_{uploaded_file.name}"):
                        with st.spinner("Processing..."):
                            # Save to temp file
                            with tempfile.NamedTemporaryFile(
                                delete=False,
                                suffix=Path(uploaded_file.name).suffix
                            ) as tmp:
                                tmp.write(uploaded_file.getvalue())
                                tmp_path = tmp.name
                            
                            try:
                                # Process
                                doc = processor.process_file(tmp_path)
                                doc.name = uploaded_file.name
                                
                                # Add to KB
                                result = kb.add_document(doc)
                                
                                st.success(f"✅ Indexed {result['chunks_added']} chunks")
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                            
                            finally:
                                os.unlink(tmp_path)
    
    st.divider()
    
    # Paste text
    st.markdown("### Or Paste Text")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        text_name = st.text_input("Document name", value="pasted_text.txt")
    with col2:
        text_type = st.selectbox(
            "Type",
            ["text", "markdown", "code"]
        )
    
    pasted_text = st.text_area(
        "Paste content here",
        height=200,
        placeholder="Paste your text, markdown, or code here..."
    )
    
    if st.button("📥 Index Text", disabled=not pasted_text):
        with st.spinner("Processing..."):
            doc_type = {
                "text": DocumentType.TEXT,
                "markdown": DocumentType.MARKDOWN,
                "code": DocumentType.CODE
            }[text_type]
            
            doc = processor.process_text(pasted_text, text_name, doc_type)
            result = kb.add_document(doc)
            
            st.success(f"✅ Indexed {result['chunks_added']} chunks")

# ============== SEARCH PAGE ==============

elif page == "🔍 Search":
    st.markdown("### Semantic Search")
    
    search_query = st.text_input(
        "Search query",
        placeholder="Search for concepts, topics, or specific information..."
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        n_results = st.slider("Number of results", 1, 20, 5)
    with col2:
        min_score = st.slider("Minimum relevance", 0.0, 1.0, 0.0)
    
    if search_query:
        results = kb.search(
            search_query,
            n_results=n_results,
            min_score=min_score
        )
        
        st.markdown(f"### Found {len(results)} results")
        
        for i, result in enumerate(results):
            with st.expander(
                f"**{result.chunk.document_name}** (chunk {result.chunk.chunk_index + 1}) - Score: {result.score:.3f}",
                expanded=(i < 3)
            ):
                st.markdown(result.chunk.content)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"Document: {result.chunk.document_name}")
                with col2:
                    st.caption(f"Chunk: {result.chunk.chunk_index + 1}/{result.chunk.total_chunks}")

# ============== DOCUMENTS PAGE ==============

elif page == "📄 Documents":
    st.markdown("### Document Library")
    
    documents = kb.list_documents()
    
    if not documents:
        st.info("📤 No documents yet. Upload some documents to get started!")
    else:
        for doc in documents:
            with st.expander(f"📄 {doc['name']}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.caption(f"**Type:** {doc.get('type', 'unknown')}")
                    st.caption(f"**Chunks:** {doc.get('chunk_count', 0)}")
                
                with col2:
                    st.caption(f"**Size:** {doc.get('content_length', 0):,} chars")
                    st.caption(f"**Indexed:** {doc.get('indexed_at', 'unknown')[:10]}")
                
                with col3:
                    if st.button("🗑️ Delete", key=f"del_{doc['id']}"):
                        kb.remove_document(doc['id'])
                        st.rerun()
                
                # Show chunks
                st.markdown("#### Chunks")
                chunks = kb.get_document_chunks(doc['id'])
                
                for chunk in chunks[:5]:  # Show first 5
                    st.text_area(
                        f"Chunk {chunk.chunk_index + 1}",
                        value=chunk.content,
                        height=100,
                        disabled=True,
                        key=f"chunk_{chunk.id}"
                    )
                
                if len(chunks) > 5:
                    st.caption(f"... and {len(chunks) - 5} more chunks")

# ============== GRAPH PAGE ==============

elif page == "🕸️ Graph":
    st.markdown("### Knowledge Graph")
    
    if stats["total_documents"] == 0:
        st.info("📤 Upload some documents to generate a knowledge graph!")
    else:
        tab1, tab2 = st.tabs(["🧠 Concept Graph", "🔗 Document Similarity"])
        
        with tab1:
            st.markdown("#### Extract concepts and relationships")
            
            if st.button("🔄 Generate Concept Graph"):
                with st.spinner("Analyzing documents..."):
                    extractor = KnowledgeGraphExtractor()
                    graph = extractor.extract_from_kb(kb, max_documents=5)
                
                if graph.nodes:
                    st.markdown("##### Mermaid Diagram")
                    mermaid_code = graph.to_mermaid()
                    st.code(mermaid_code, language="mermaid")
                    
                    st.markdown("##### Graph Data")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Nodes**")
                        for node in graph.nodes:
                            icon = "📄" if node.type == "document" else "💡"
                            st.markdown(f"{icon} {node.label} ({node.type})")
                    
                    with col2:
                        st.markdown("**Relationships**")
                        for edge in graph.edges:
                            st.markdown(f"• {edge.source} → *{edge.relationship}* → {edge.target}")
                else:
                    st.warning("Could not extract graph. Try adding more documents.")
        
        with tab2:
            st.markdown("#### Document similarity network")
            
            similarity_threshold = st.slider(
                "Similarity threshold",
                0.0, 1.0, 0.3,
                help="Higher = fewer connections"
            )
            
            if st.button("🔄 Generate Similarity Graph"):
                with st.spinner("Computing similarities..."):
                    sim_graph = DocumentSimilarityGraph(kb)
                    graph = sim_graph.build(similarity_threshold)
                
                if graph.nodes:
                    st.markdown("##### Document Network")
                    
                    # Simple visualization
                    st.markdown("**Documents:**")
                    for node in graph.nodes:
                        chunks = node.metadata.get("chunks", 0)
                        st.markdown(f"• 📄 {node.label} ({chunks} chunks)")
                    
                    st.markdown("**Connections:**")
                    if graph.edges:
                        for edge in graph.edges:
                            src_label = next((n.label for n in graph.nodes if n.id == edge.source), edge.source)
                            tgt_label = next((n.label for n in graph.nodes if n.id == edge.target), edge.target)
                            st.markdown(f"• {src_label} ↔ {tgt_label} (similarity: {edge.weight:.2f})")
                    else:
                        st.info("No documents are similar enough with current threshold")
                else:
                    st.warning("Not enough documents for similarity analysis")

# ============== FOOTER ==============

st.divider()
st.caption("📚 Personal Knowledge Base | Project 4.1 | learn-agentic-stack")
