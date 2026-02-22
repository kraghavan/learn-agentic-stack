"""
Observable Agent - Project 2.4
A fully observable AI agent with metrics, logging, and dashboards.
"""

import os
import time
import uuid
from datetime import datetime

import streamlit as st
from anthropic import Anthropic

from metrics_collector import get_collector, track_api_call, track_tool
from structured_logger import get_logger

# Initialize
claude = Anthropic()
metrics = get_collector()
logger = get_logger()


# ============== OBSERVABLE WRAPPER ==============

def chat_with_observation(
    messages: list,
    session_id: str,
    model: str = "claude-sonnet-4-20250514"
) -> dict:
    """
    Chat with Claude with full observability.
    Records metrics and logs for every call.
    """
    start_time = time.time()
    
    # Log the request
    logger.log_user_message(
        session_id=session_id,
        message_preview=messages[-1]["content"] if messages else ""
    )
    
    try:
        # Make API call
        response = claude.messages.create(
            model=model,
            max_tokens=1000,
            messages=messages
        )
        
        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        
        # Record metrics
        result = metrics.record_api_call(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=True
        )
        
        # Log the response
        logger.log_api_call(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=True
        )
        
        logger.log_agent_response(
            session_id=session_id,
            latency_ms=latency_ms,
            tokens=output_tokens
        )
        
        return {
            "content": response.content[0].text,
            "metrics": result,
            "success": True
        }
    
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        
        # Record error metrics
        metrics.record_api_call(
            model=model,
            input_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
            success=False,
            error=str(e)
        )
        
        metrics.record_error(
            error_type=type(e).__name__,
            error_message=str(e),
            component="api"
        )
        
        # Log error
        logger.error(
            "API call failed",
            error=str(e),
            model=model,
            latency_ms=latency_ms
        )
        
        return {
            "content": f"Error: {str(e)}",
            "metrics": {"error": str(e)},
            "success": False
        }


# ============== SAMPLE TOOLS ==============

def search_tool(query: str) -> str:
    """Simulated search tool with observability."""
    with track_tool("search"):
        # Simulate search latency
        time.sleep(0.3)
        logger.log_tool_use(
            tool="search",
            latency_ms=300,
            success=True
        )
        return f"Search results for: {query}"


def calculator_tool(expression: str) -> str:
    """Simulated calculator tool with observability."""
    with track_tool("calculator"):
        try:
            result = eval(expression)  # Don't do this in production!
            logger.log_tool_use(
                tool="calculator",
                latency_ms=10,
                success=True
            )
            return str(result)
        except Exception as e:
            logger.log_tool_use(
                tool="calculator",
                latency_ms=10,
                success=False,
                error=str(e)
            )
            raise


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="Observable Agent",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Observable Agent")
st.markdown("*Full observability with metrics, logs, and dashboards*")

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
    logger.log_session_start(st.session_state.session_id)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "session_start" not in st.session_state:
    st.session_state.session_start = time.time()

# Sidebar
with st.sidebar:
    st.header("📊 Live Metrics")
    
    # Connection status
    col1, col2 = st.columns(2)
    with col1:
        if metrics.is_connected():
            st.success("InfluxDB ✓")
        else:
            st.error("InfluxDB ✗")
    with col2:
        st.info(f"Session: {st.session_state.session_id}")
    
    st.divider()
    
    # Session metrics
    st.subheader("📈 This Session")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", len(st.session_state.messages))
    with col2:
        st.metric("Tokens", st.session_state.total_tokens)
    
    col1, col2 = st.columns(2)
    with col1:
        duration = int(time.time() - st.session_state.session_start)
        st.metric("Duration", f"{duration}s")
    with col2:
        st.metric("Cost", f"${st.session_state.total_cost:.4f}")
    
    st.divider()
    
    # Links to dashboards
    st.subheader("🔗 Dashboards")
    
    st.markdown("[📊 Grafana Dashboard](http://localhost:3000)")
    st.caption("Login: admin / admin")
    
    st.markdown("[📈 InfluxDB UI](http://localhost:8086)")
    st.caption("Login: admin / adminpassword")
    
    st.divider()
    
    # Recent metrics from InfluxDB
    st.subheader("📉 24h Stats")
    
    if metrics.is_connected():
        total_cost = metrics.get_total_cost(hours=24)
        st.metric("Total Cost (24h)", f"${total_cost:.4f}")
    else:
        st.caption("Connect to InfluxDB to see stats")
    
    st.divider()
    
    # Session controls
    if st.button("🔄 New Session", use_container_width=True):
        # Log session end
        duration = time.time() - st.session_state.session_start
        logger.log_session_end(
            session_id=st.session_state.session_id,
            duration_seconds=duration,
            message_count=len(st.session_state.messages)
        )
        
        # Reset
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.session_state.total_cost = 0.0
        st.session_state.session_start = time.time()
        
        # Log new session
        logger.log_session_start(st.session_state.session_id)
        
        st.rerun()

# Main content
tab1, tab2 = st.tabs(["💬 Chat", "📊 Metrics View"])

with tab1:
    # Chat display
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
            # Show metrics for assistant messages
            if msg["role"] == "assistant" and msg.get("metrics"):
                m = msg["metrics"]
                if m.get("success", True):
                    st.caption(
                        f"📊 {m.get('total_tokens', 0)} tokens | "
                        f"{m.get('latency_ms', 0):.0f}ms | "
                        f"${m.get('cost_usd', 0):.5f}"
                    )
    
    # Chat input
    if prompt := st.chat_input("Say something..."):
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get response with observability
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Build messages for API
                api_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
                
                result = chat_with_observation(
                    messages=api_messages,
                    session_id=st.session_state.session_id
                )
            
            st.write(result["content"])
            
            # Show metrics
            if result.get("metrics") and result.get("success"):
                m = result["metrics"]
                st.caption(
                    f"📊 {m.get('total_tokens', 0)} tokens | "
                    f"{m.get('latency_ms', 0):.0f}ms | "
                    f"${m.get('cost_usd', 0):.5f}"
                )
                
                # Update session totals
                st.session_state.total_tokens += m.get("total_tokens", 0)
                st.session_state.total_cost += m.get("cost_usd", 0)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["content"],
            "metrics": result.get("metrics")
        })

with tab2:
    st.subheader("📊 Real-time Metrics")
    
    st.markdown("""
    ### Grafana Dashboard
    
    Open [http://localhost:3000](http://localhost:3000) to see:
    
    - **API Calls** - Count, latency, success rate
    - **Token Usage** - Input vs output tokens over time
    - **Cost Tracking** - Running costs by model
    - **Error Rates** - Failures and error types
    - **Logs** - Structured logs from Loki
    
    ### InfluxDB
    
    Open [http://localhost:8086](http://localhost:8086) to query raw metrics.
    
    ### What's Being Tracked
    
    | Metric | Fields |
    |--------|--------|
    | `api_call` | model, tokens, latency, cost, success |
    | `tool_use` | tool, latency, success, error |
    | `memory_operation` | operation, collection, latency |
    | `session` | session_id, event, duration |
    | `error` | type, message, component |
    | `cost` | amount_usd, category |
    """)
    
    st.divider()
    
    # Simple metrics display
    st.subheader("📈 Session Breakdown")
    
    if st.session_state.messages:
        import pandas as pd
        
        # Build metrics table
        metrics_data = []
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "assistant" and msg.get("metrics"):
                m = msg["metrics"]
                metrics_data.append({
                    "Message #": i // 2 + 1,
                    "Tokens": m.get("total_tokens", 0),
                    "Latency (ms)": round(m.get("latency_ms", 0), 0),
                    "Cost ($)": round(m.get("cost_usd", 0), 5),
                })
        
        if metrics_data:
            df = pd.DataFrame(metrics_data)
            st.dataframe(df, use_container_width=True)
            
            # Summary
            st.markdown(f"""
            **Totals:**
            - Total Tokens: {sum(d['Tokens'] for d in metrics_data)}
            - Avg Latency: {sum(d['Latency (ms)'] for d in metrics_data) / len(metrics_data):.0f}ms
            - Total Cost: ${sum(d['Cost ($)'] for d in metrics_data):.5f}
            """)
    else:
        st.info("Start chatting to see metrics!")

# Footer
st.divider()
st.caption("Project 2.4 - Observable Agent | learn-agentic-stack")
