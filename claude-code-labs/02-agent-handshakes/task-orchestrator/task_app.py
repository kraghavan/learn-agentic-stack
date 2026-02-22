"""
Task Decomposition UI - Project 3.4
Streamlit interface for hierarchical task orchestration.
"""

import streamlit as st
import time

from task_orchestrator import (
    execute_task, run_orchestrator_plan, run_worker, run_orchestrator_aggregate,
    TaskPlan, SubTask, TaskStatus, WorkerType, SAMPLE_TASKS
)


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="Task Orchestrator",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Task Decomposition Orchestrator")
st.markdown("*Hierarchical pattern: Master agent delegates to specialized workers*")

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "task" not in st.session_state:
    st.session_state.task = ""
if "plan" not in st.session_state:
    st.session_state.plan = None
if "current_subtask_idx" not in st.session_state:
    st.session_state.current_subtask_idx = 0
if "results" not in st.session_state:
    st.session_state.results = {}
if "final_output" not in st.session_state:
    st.session_state.final_output = ""
if "metadata" not in st.session_state:
    st.session_state.metadata = {"total_tokens": 0, "start_time": 0}

# Sidebar
with st.sidebar:
    st.header("🎯 How It Works")
    
    st.markdown("""
    ### The Pattern
    
    ```
         ┌─────────────┐
         │ Orchestrator│
         │  (Planner)  │
         └──────┬──────┘
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
    ┌──────┐ ┌──────┐ ┌──────┐
    │Worker│ │Worker│ │Worker│
    │  A   │ │  B   │ │  C   │
    └──┬───┘ └──┬───┘ └──┬───┘
       │        │        │
       └────────┼────────┘
                ▼
         ┌─────────────┐
         │ Orchestrator│
         │ (Aggregator)│
         └─────────────┘
    ```
    
    ### Worker Types
    
    🔍 **Research** - Gather info
    💻 **Code** - Write code
    ✍️ **Write** - Create content
    📊 **Analyze** - Analyze data
    📝 **Summarize** - Condense info
    
    ### Key Concepts
    
    **Decomposition:**
    Complex task → Subtasks
    
    **Delegation:**
    Each subtask → Specialist
    
    **Aggregation:**
    All results → Final output
    
    **Dependencies:**
    Some tasks wait for others
    """)
    
    st.divider()
    st.caption("Project 3.4 | learn-agentic-stack")

# Main content
if st.session_state.stage == "input":
    st.markdown("### Enter a Complex Task")
    
    # Sample tasks
    st.markdown("**Sample Tasks:**")
    for i, task in enumerate(SAMPLE_TASKS):
        if st.button(task[:80] + "...", key=f"sample_{i}", use_container_width=True):
            st.session_state.task = task
            st.rerun()
    
    st.divider()
    
    # Custom task
    st.markdown("**Or enter your own:**")
    custom_task = st.text_area(
        "Complex Task",
        value=st.session_state.task,
        height=100,
        placeholder="e.g., 'Create a technical blog post about...' or 'Build a project proposal for...'"
    )
    
    if custom_task:
        st.session_state.task = custom_task
    
    # Start button
    if st.button("🎯 Start Orchestration", type="primary", disabled=not st.session_state.task):
        st.session_state.stage = "planning"
        st.session_state.metadata["start_time"] = time.time()
        st.rerun()

elif st.session_state.stage == "planning":
    st.markdown("### 📋 Orchestrator Planning...")
    
    task = st.session_state.task
    st.info(f"**Task:** {task}")
    
    with st.spinner("Breaking down task into subtasks..."):
        plan, meta = run_orchestrator_plan(task)
        st.session_state.plan = plan
        st.session_state.metadata["total_tokens"] += meta["input_tokens"] + meta["output_tokens"]
    
    st.session_state.stage = "show_plan"
    st.rerun()

elif st.session_state.stage == "show_plan":
    plan = st.session_state.plan
    
    st.markdown("### 📋 Task Decomposition Plan")
    st.success(f"**Goal:** {plan.goal}")
    
    # Show task tree
    st.markdown("#### Subtasks")
    
    for i, subtask in enumerate(plan.subtasks):
        worker_icons = {
            WorkerType.RESEARCH: "🔍",
            WorkerType.CODE: "💻",
            WorkerType.WRITE: "✍️",
            WorkerType.ANALYZE: "📊",
            WorkerType.SUMMARIZE: "📝"
        }
        icon = worker_icons.get(subtask.worker_type, "📌")
        
        deps = f" (depends on: {', '.join(subtask.dependencies)})" if subtask.dependencies else ""
        
        st.markdown(f"""
        **{i+1}. {icon} {subtask.title}** `[{subtask.worker_type.value}]`{deps}
        > {subtask.description}
        """)
    
    # Execution order visualization
    st.markdown("#### Execution Order")
    
    for i, group in enumerate(plan.execution_order):
        if len(group) > 1:
            st.markdown(f"**Phase {i+1}** (parallel): {', '.join(group)}")
        else:
            st.markdown(f"**Phase {i+1}**: {group[0]}")
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🚀 Execute Plan", type="primary"):
            st.session_state.stage = "executing"
            st.session_state.current_subtask_idx = 0
            st.session_state.results = {}
            st.rerun()
    with col2:
        if st.button("✏️ Modify Task"):
            st.session_state.stage = "input"
            st.session_state.plan = None
            st.rerun()

elif st.session_state.stage == "executing":
    plan = st.session_state.plan
    
    st.markdown("### ⚙️ Executing Subtasks")
    
    # Progress
    completed = len(st.session_state.results)
    total = len(plan.subtasks)
    progress = completed / total
    st.progress(progress, text=f"Progress: {completed}/{total} subtasks")
    
    # Show all subtasks with status
    cols = st.columns(min(len(plan.subtasks), 4))
    for i, subtask in enumerate(plan.subtasks):
        with cols[i % len(cols)]:
            if subtask.id in st.session_state.results:
                st.success(f"✅ {subtask.title}")
            elif subtask.status == TaskStatus.IN_PROGRESS:
                st.info(f"⏳ {subtask.title}")
            else:
                st.warning(f"⏸️ {subtask.title}")
    
    st.divider()
    
    # Execute next subtask(s)
    for group in plan.execution_order:
        group_done = all(task_id in st.session_state.results for task_id in group)
        if group_done:
            continue
        
        for task_id in group:
            if task_id in st.session_state.results:
                continue
            
            subtask = next((s for s in plan.subtasks if s.id == task_id), None)
            if not subtask:
                continue
            
            deps_met = all(dep in st.session_state.results for dep in subtask.dependencies)
            if not deps_met:
                continue
            
            subtask.status = TaskStatus.IN_PROGRESS
            
            worker_icons = {
                WorkerType.RESEARCH: "🔍",
                WorkerType.CODE: "💻",
                WorkerType.WRITE: "✍️",
                WorkerType.ANALYZE: "📊",
                WorkerType.SUMMARIZE: "📝"
            }
            icon = worker_icons.get(subtask.worker_type, "📌")
            
            with st.spinner(f"{icon} {subtask.worker_type.value.title()} Worker: {subtask.title}"):
                dep_results = {dep: st.session_state.results.get(dep, "") for dep in subtask.dependencies}
                result, meta = run_worker(subtask, "", dep_results)
                
                subtask.result = result
                subtask.status = TaskStatus.COMPLETED
                st.session_state.results[task_id] = result
                st.session_state.metadata["total_tokens"] += meta["input_tokens"] + meta["output_tokens"]
            
            st.rerun()
        
        break
    
    if len(st.session_state.results) == len(plan.subtasks):
        st.session_state.stage = "aggregating"
        st.rerun()

elif st.session_state.stage == "aggregating":
    plan = st.session_state.plan
    
    st.markdown("### 🔄 Aggregating Results...")
    
    with st.expander("📋 Completed Subtasks", expanded=False):
        for subtask in plan.subtasks:
            st.markdown(f"**{subtask.title}**")
            st.text(subtask.result[:500] + "..." if len(subtask.result) > 500 else subtask.result)
            st.divider()
    
    with st.spinner("Orchestrator combining results into final output..."):
        final_output, meta = run_orchestrator_aggregate(
            plan.original_task,
            plan.goal,
            st.session_state.results
        )
        st.session_state.final_output = final_output
        st.session_state.metadata["total_tokens"] += meta["input_tokens"] + meta["output_tokens"]
    
    st.session_state.stage = "complete"
    st.rerun()

elif st.session_state.stage == "complete":
    plan = st.session_state.plan
    
    execution_time = time.time() - st.session_state.metadata["start_time"]
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Subtasks", len(plan.subtasks))
    with col2:
        st.metric("Workers Used", len(set(s.worker_type for s in plan.subtasks)))
    with col3:
        st.metric("Time", f"{execution_time:.1f}s")
    with col4:
        cost = st.session_state.metadata["total_tokens"] * 0.000009
        st.metric("Est. Cost", f"${cost:.4f}")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Final Output", "🌳 Task Tree", "📊 Subtask Results", "📈 Metrics"])
    
    with tab1:
        st.markdown("## Final Output")
        st.markdown(st.session_state.final_output)
        
        st.divider()
        st.download_button(
            "📥 Download Output",
            st.session_state.final_output,
            file_name="task_output.md",
            mime="text/markdown"
        )
    
    with tab2:
        st.markdown("## Task Decomposition Tree")
        
        st.markdown(f"### 🎯 {plan.original_task[:100]}...")
        st.markdown(f"**Goal:** {plan.goal}")
        
        st.divider()
        
        for phase_idx, group in enumerate(plan.execution_order):
            st.markdown(f"#### Phase {phase_idx + 1}" + (" (parallel)" if len(group) > 1 else ""))
            
            cols = st.columns(len(group))
            for i, task_id in enumerate(group):
                subtask = next((s for s in plan.subtasks if s.id == task_id), None)
                if subtask:
                    with cols[i]:
                        worker_icons = {
                            WorkerType.RESEARCH: "🔍",
                            WorkerType.CODE: "💻",
                            WorkerType.WRITE: "✍️",
                            WorkerType.ANALYZE: "📊",
                            WorkerType.SUMMARIZE: "📝"
                        }
                        icon = worker_icons.get(subtask.worker_type, "📌")
                        
                        st.success(f"""
                        **{icon} {subtask.title}**
                        
                        `{subtask.worker_type.value}`
                        """)
                        
                        if subtask.dependencies:
                            st.caption(f"↑ Depends on: {', '.join(subtask.dependencies)}")
    
    with tab3:
        st.markdown("## Subtask Results")
        
        for subtask in plan.subtasks:
            worker_icons = {
                WorkerType.RESEARCH: "🔍",
                WorkerType.CODE: "💻",
                WorkerType.WRITE: "✍️",
                WorkerType.ANALYZE: "📊",
                WorkerType.SUMMARIZE: "📝"
            }
            icon = worker_icons.get(subtask.worker_type, "📌")
            
            with st.expander(f"{icon} {subtask.title} [{subtask.worker_type.value}]"):
                st.markdown(f"**Description:** {subtask.description}")
                st.divider()
                st.markdown("**Result:**")
                st.markdown(subtask.result)
    
    with tab4:
        st.markdown("## Execution Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Token Usage")
            st.metric("Total Tokens", st.session_state.metadata["total_tokens"])
            
            st.markdown("**API Calls:**")
            st.markdown(f"- Planning: 1 call")
            st.markdown(f"- Workers: {len(plan.subtasks)} calls")
            st.markdown(f"- Aggregation: 1 call")
            st.markdown(f"- **Total: {len(plan.subtasks) + 2} calls**")
        
        with col2:
            st.markdown("### Worker Distribution")
            worker_counts = {}
            for s in plan.subtasks:
                wt = s.worker_type.value
                worker_counts[wt] = worker_counts.get(wt, 0) + 1
            
            for wt, count in worker_counts.items():
                st.markdown(f"- **{wt}**: {count} task(s)")
        
        st.divider()
        
        st.markdown("### Execution Timeline")
        st.markdown(f"- **Planning:** ~2-3s")
        for phase_idx, group in enumerate(plan.execution_order):
            parallel_note = " (parallel)" if len(group) > 1 else ""
            st.markdown(f"- **Phase {phase_idx + 1}:** {', '.join(group)}{parallel_note}")
        st.markdown(f"- **Aggregation:** ~2-3s")
        st.markdown(f"- **Total Time:** {execution_time:.1f}s")
    
    # Reset button
    st.divider()
    if st.button("🔄 New Task", type="primary"):
        st.session_state.stage = "input"
        st.session_state.task = ""
        st.session_state.plan = None
        st.session_state.results = {}
        st.session_state.final_output = ""
        st.session_state.metadata = {"total_tokens": 0, "start_time": 0}
        st.rerun()
