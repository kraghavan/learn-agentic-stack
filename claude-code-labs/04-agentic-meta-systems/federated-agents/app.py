"""
Control Plane UI - Project 5.3
Streamlit dashboard for federated agent system.
"""

import os
import json
import time
import streamlit as st
from datetime import datetime

from message_schema import AgentMessage, AgentType, MessageType, TaskType, Priority, SAMPLE_MESSAGES
from message_queue import MessageQueue
from orchestrator import Orchestrator, TaskStatus


# ============== PAGE CONFIG ==============

st.set_page_config(
    page_title="Federated Agents",
    page_icon="🌐",
    layout="wide"
)

# ============== SESSION STATE ==============

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
if "connected" not in st.session_state:
    st.session_state.connected = False

# ============== SIDEBAR ==============

with st.sidebar:
    st.title("🌐 Federated Agents")
    st.markdown("---")
    
    # Connection status
    if st.session_state.connected:
        st.success("✅ Connected to RabbitMQ")
    else:
        st.warning("⚠️ Not connected")
    
    # Connect button
    if not st.session_state.connected:
        rabbitmq_host = st.text_input("RabbitMQ Host", value=os.getenv("RABBITMQ_HOST", "localhost"))
        
        if st.button("🔌 Connect", use_container_width=True):
            os.environ["RABBITMQ_HOST"] = rabbitmq_host
            orchestrator = Orchestrator()
            if orchestrator.connect():
                orchestrator.start_listener()
                st.session_state.orchestrator = orchestrator
                st.session_state.connected = True
                st.rerun()
            else:
                st.error("Failed to connect")
    else:
        if st.button("🔌 Disconnect", use_container_width=True):
            if st.session_state.orchestrator:
                st.session_state.orchestrator.disconnect()
            st.session_state.orchestrator = None
            st.session_state.connected = False
            st.rerun()
    
    st.markdown("---")
    st.markdown("### Architecture")
    st.code("""
┌─────────────────┐
│  Control Plane  │
└────────┬────────┘
         │
    ┌────┴────┐
    │ RabbitMQ│
    └────┬────┘
    ┌────┴────┬────────┐
    ▼         ▼        ▼
┌───────┐ ┌───────┐ ┌───────┐
│Claude │ │OpenAI │ │Gemini │
│(Local)│ │(Local)│ │(Cloud)│
└───────┘ └───────┘ └───────┘
    """, language=None)

# ============== MAIN CONTENT ==============

st.title("🌐 Federated Multi-Agent Control Plane")

if not st.session_state.connected:
    st.info("👈 Connect to RabbitMQ to start")
    
    st.markdown("### 📋 Sample Message Schema")
    for name, msg in SAMPLE_MESSAGES.items():
        with st.expander(f"📨 {name.replace('_', ' ').title()}"):
            st.json(json.loads(msg.to_json()))

else:
    orchestrator = st.session_state.orchestrator
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🚀 Submit Task", "📜 History"])
    
    with tab1:
        st.markdown("### Agent Status")
        
        health = orchestrator.check_agent_health()
        queue_stats = orchestrator.mq.get_queue_stats()
        
        col1, col2, col3 = st.columns(3)
        
        agents_info = [
            ("🤖 Claude (Local)", AgentType.LOCAL_CLAUDE, "Code review, Architecture"),
            ("💬 OpenAI (Local)", AgentType.LOCAL_OPENAI, "Content, Brainstorming"),
            ("☁️ Gemini (Cloud)", AgentType.CLOUD_GEMINI, "Research, Data analysis")
        ]
        
        for col, (name, agent_type, specialty) in zip([col1, col2, col3], agents_info):
            with col:
                status = health.get(agent_type.value, "unknown")
                stats = queue_stats.get(agent_type.value, {})
                
                if status == "healthy":
                    st.success(f"**{name}**")
                else:
                    st.warning(f"**{name}**")
                
                st.caption(f"Specialty: {specialty}")
                st.caption(f"Queue: {stats.get('messages', 0)} msgs")
        
        st.markdown("---")
        st.markdown("### Recent Tasks")
        
        tasks = orchestrator.get_all_tasks()[-5:]
        if not tasks:
            st.info("No tasks submitted yet")
        else:
            for task in reversed(tasks):
                icon = {"pending": "⏳", "processing": "🔄", "completed": "✅", "failed": "❌"}.get(task.status, "❓")
                with st.expander(f"{icon} {task.task_type.value} → {task.target_agent.value}"):
                    st.text(f"ID: {task.task_id[:8]}... | Status: {task.status}")
                    if task.result:
                        st.json(task.result)
    
    with tab2:
        st.markdown("### Submit Task to Agent")
        
        col1, col2 = st.columns(2)
        
        with col1:
            target_agent = st.selectbox(
                "Target Agent",
                options=[AgentType.LOCAL_CLAUDE, AgentType.LOCAL_OPENAI, AgentType.CLOUD_GEMINI],
                format_func=lambda x: {
                    AgentType.LOCAL_CLAUDE: "🤖 Claude (Local)",
                    AgentType.LOCAL_OPENAI: "💬 OpenAI (Local)",
                    AgentType.CLOUD_GEMINI: "☁️ Gemini (Cloud)"
                }[x]
            )
        
        with col2:
            if target_agent == AgentType.LOCAL_CLAUDE:
                task_options = [TaskType.CODE_REVIEW, TaskType.ARCHITECTURE_DESIGN]
            elif target_agent == AgentType.LOCAL_OPENAI:
                task_options = [TaskType.CONTENT_GENERATION, TaskType.BRAINSTORMING]
            else:
                task_options = [TaskType.DATA_ANALYSIS, TaskType.WEB_RESEARCH]
            
            task_type = st.selectbox("Task Type", options=task_options)
        
        st.markdown("### Payload")
        
        if task_type == TaskType.CODE_REVIEW:
            code = st.text_area("Code", height=150, value="def hello():\n    print('world')")
            payload = {"code": code, "language": "python"}
        elif task_type == TaskType.CONTENT_GENERATION:
            topic = st.text_input("Topic", value="Benefits of microservices")
            payload = {"topic": topic, "format": "blog_post"}
        elif task_type == TaskType.BRAINSTORMING:
            topic = st.text_input("Topic", value="New features")
            payload = {"topic": topic, "ideas": 5}
        elif task_type == TaskType.WEB_RESEARCH:
            query = st.text_input("Query", value="AI trends 2024")
            payload = {"query": query}
        else:
            payload = {"prompt": st.text_area("Prompt")}
        
        if st.button("🚀 Submit", type="primary", use_container_width=True):
            task_id = orchestrator.submit_task(target_agent, task_type, payload)
            if task_id:
                st.success(f"✅ Submitted: {task_id[:8]}...")
                with st.spinner("Waiting..."):
                    result = orchestrator.wait_for_task(task_id, timeout=30)
                if result:
                    st.json(result)
    
    with tab3:
        if st.button("🔄 Refresh"):
            st.rerun()
        
        for task in reversed(orchestrator.get_all_tasks()):
            st.markdown(f"**{task.task_type.value}** → {task.target_agent.value} [{task.status}]")
            if task.result:
                with st.expander("Result"):
                    st.json(task.result)

st.markdown("---")
st.caption("🌐 Federated Agents | Project 5.3 | learn-agentic-stack")