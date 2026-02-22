"""
Debate Agents UI - Project 3.3
Streamlit interface for adversarial debate between Pro and Con agents.
"""

import streamlit as st
import time

from debate_orchestrator import (
    run_pro_agent, run_con_agent, run_synthesizer,
    Argument, Synthesis, SAMPLE_TOPICS
)


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="Debate Agents",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Debate Agents")
st.markdown("*Adversarial pattern: Pro vs Con with balanced synthesis*")

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "num_rounds" not in st.session_state:
    st.session_state.num_rounds = 3
if "current_round" not in st.session_state:
    st.session_state.current_round = 0
if "arguments" not in st.session_state:
    st.session_state.arguments = []
if "synthesis" not in st.session_state:
    st.session_state.synthesis = None
if "metadata" not in st.session_state:
    st.session_state.metadata = {"total_input": 0, "total_output": 0}

# Sidebar
with st.sidebar:
    st.header("⚖️ How It Works")
    
    st.markdown("""
    ### The Agents
    
    **🟢 Pro Agent**
    - Argues IN FAVOR
    - Builds case over rounds
    - Responds to Con rebuttals
    
    **🔴 Con Agent**
    - Argues AGAINST
    - Challenges Pro's points
    - Presents counter-evidence
    
    **⚖️ Synthesizer**
    - Analyzes both sides
    - Identifies common ground
    - Provides nuanced conclusion
    
    ### The Pattern
    
    ```
    Round 1:
      🟢 Pro opens
      🔴 Con responds
    
    Round 2:
      🟢 Pro rebuts
      🔴 Con counters
    
    Round 3:
      🟢 Pro strengthens
      🔴 Con concludes
    
    ⚖️ Synthesis
    ```
    
    ### Key Concept
    
    **Adversarial prompting** creates better outputs by:
    - Exploring both sides
    - Stress-testing arguments
    - Avoiding one-sided bias
    """)
    
    st.divider()
    st.caption("Project 3.3 | learn-agentic-stack")

# Main content
if st.session_state.stage == "input":
    st.markdown("### Choose a Debate Topic")
    
    # Sample topics
    st.markdown("**Sample Topics:**")
    cols = st.columns(2)
    for i, topic in enumerate(SAMPLE_TOPICS):
        with cols[i % 2]:
            if st.button(topic, key=f"topic_{i}", use_container_width=True):
                st.session_state.topic = topic
                st.rerun()
    
    st.divider()
    
    # Custom topic
    st.markdown("**Or enter your own:**")
    custom_topic = st.text_input(
        "Debate Topic",
        value=st.session_state.topic,
        placeholder="e.g., 'AI regulation should be increased' or 'Pineapple belongs on pizza'"
    )
    
    if custom_topic:
        st.session_state.topic = custom_topic
    
    # Settings
    st.markdown("### Settings")
    num_rounds = st.slider("Number of Rounds", 1, 5, 3)
    st.session_state.num_rounds = num_rounds
    
    st.caption(f"Total exchanges: {num_rounds * 2} (Pro and Con each round)")
    
    # Start button
    if st.button("🎯 Start Debate", type="primary", disabled=not st.session_state.topic):
        st.session_state.stage = "debating"
        st.session_state.current_round = 1
        st.session_state.arguments = []
        st.session_state.metadata = {"total_input": 0, "total_output": 0}
        st.rerun()

elif st.session_state.stage == "debating":
    topic = st.session_state.topic
    current_round = st.session_state.current_round
    num_rounds = st.session_state.num_rounds
    arguments = st.session_state.arguments
    
    # Progress
    total_steps = num_rounds * 2 + 1  # rounds * 2 agents + synthesis
    current_step = len(arguments)
    progress = current_step / total_steps
    
    st.progress(progress, text=f"Round {current_round} of {num_rounds}")
    
    st.markdown(f"### Topic: *{topic}*")
    st.divider()
    
    # Show previous arguments
    if arguments:
        for arg in arguments:
            if arg.side == "pro":
                with st.chat_message("assistant", avatar="🟢"):
                    st.markdown(f"**PRO - Round {arg.round}**")
                    st.markdown(arg.main_point)
                    if arg.supporting_points:
                        for point in arg.supporting_points:
                            st.markdown(f"• {point}")
                    if arg.rebuttal_to:
                        st.caption(f"↩️ *Rebuttal: {arg.rebuttal_to}*")
            else:
                with st.chat_message("user", avatar="🔴"):
                    st.markdown(f"**CON - Round {arg.round}**")
                    st.markdown(arg.main_point)
                    if arg.supporting_points:
                        for point in arg.supporting_points:
                            st.markdown(f"• {point}")
                    if arg.rebuttal_to:
                        st.caption(f"↩️ *Rebuttal: {arg.rebuttal_to}*")
    
    # Determine what's next
    args_in_round = len([a for a in arguments if a.round == current_round])
    
    if args_in_round == 0:
        # Pro's turn
        with st.chat_message("assistant", avatar="🟢"):
            with st.spinner("🟢 Pro is formulating argument..."):
                start_time = time.time()
                pro_arg, meta = run_pro_agent(topic, current_round, arguments)
                elapsed = time.time() - start_time
            
            st.session_state.arguments.append(pro_arg)
            st.session_state.metadata["total_input"] += meta["input_tokens"]
            st.session_state.metadata["total_output"] += meta["output_tokens"]
            st.rerun()
    
    elif args_in_round == 1:
        # Con's turn
        with st.chat_message("user", avatar="🔴"):
            with st.spinner("🔴 Con is preparing rebuttal..."):
                start_time = time.time()
                con_arg, meta = run_con_agent(topic, current_round, arguments)
                elapsed = time.time() - start_time
            
            st.session_state.arguments.append(con_arg)
            st.session_state.metadata["total_input"] += meta["input_tokens"]
            st.session_state.metadata["total_output"] += meta["output_tokens"]
            
            # Check if more rounds
            if current_round < num_rounds:
                st.session_state.current_round += 1
                st.rerun()
            else:
                st.session_state.stage = "synthesizing"
                st.rerun()

elif st.session_state.stage == "synthesizing":
    topic = st.session_state.topic
    arguments = st.session_state.arguments
    
    st.markdown(f"### Topic: *{topic}*")
    st.divider()
    
    # Show all arguments collapsed
    with st.expander("📜 Full Debate Transcript", expanded=False):
        for arg in arguments:
            icon = "🟢" if arg.side == "pro" else "🔴"
            side = "PRO" if arg.side == "pro" else "CON"
            st.markdown(f"**{icon} {side} (Round {arg.round}):** {arg.main_point}")
    
    # Synthesis
    st.markdown("### ⚖️ Synthesizing...")
    
    with st.spinner("Analyzing both perspectives and forming balanced conclusion..."):
        synthesis, meta = run_synthesizer(topic, arguments)
        st.session_state.synthesis = synthesis
        st.session_state.metadata["total_input"] += meta["input_tokens"]
        st.session_state.metadata["total_output"] += meta["output_tokens"]
    
    st.session_state.stage = "complete"
    st.rerun()

elif st.session_state.stage == "complete":
    topic = st.session_state.topic
    arguments = st.session_state.arguments
    synthesis = st.session_state.synthesis
    
    st.markdown(f"### Topic: *{topic}*")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["⚖️ Synthesis", "📜 Full Debate", "📊 Analysis", "📈 Metrics"])
    
    with tab1:
        st.markdown("## Balanced Analysis")
        
        st.markdown(f"**Summary:** {synthesis.summary}")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🟢 Pro Strengths")
            for point in synthesis.pro_strengths:
                st.markdown(f"✓ {point}")
        
        with col2:
            st.markdown("### 🔴 Con Strengths")
            for point in synthesis.con_strengths:
                st.markdown(f"✓ {point}")
        
        st.divider()
        
        if synthesis.areas_of_agreement:
            st.markdown("### 🤝 Areas of Agreement")
            for point in synthesis.areas_of_agreement:
                st.markdown(f"• {point}")
        
        if synthesis.key_tensions:
            st.markdown("### ⚡ Key Tensions")
            for tension in synthesis.key_tensions:
                st.markdown(f"• {tension}")
        
        st.divider()
        
        st.markdown("### 📝 Nuanced Conclusion")
        st.info(synthesis.nuanced_conclusion)
        
        st.markdown("### 💡 Recommendation")
        st.success(synthesis.recommendation)
    
    with tab2:
        st.markdown("## Full Debate Transcript")
        
        for i, arg in enumerate(arguments):
            if arg.side == "pro":
                st.markdown(f"---")
                st.markdown(f"### 🟢 PRO - Round {arg.round}")
            else:
                st.markdown(f"### 🔴 CON - Round {arg.round}")
            
            st.markdown(f"**Main Point:** {arg.main_point}")
            
            if arg.supporting_points:
                st.markdown("**Supporting Points:**")
                for point in arg.supporting_points:
                    st.markdown(f"• {point}")
            
            if arg.evidence:
                st.markdown("**Evidence:**")
                for ev in arg.evidence:
                    st.markdown(f"📌 {ev}")
            
            if arg.rebuttal_to:
                st.markdown(f"**Rebuttal:** ↩️ {arg.rebuttal_to}")
    
    with tab3:
        st.markdown("## Debate Analysis")
        
        # Count arguments by type
        pro_args = [a for a in arguments if a.side == "pro"]
        con_args = [a for a in arguments if a.side == "con"]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rounds", len(pro_args))
        with col2:
            st.metric("Pro Arguments", sum(len(a.supporting_points) for a in pro_args) + len(pro_args))
        with col3:
            st.metric("Con Arguments", sum(len(a.supporting_points) for a in con_args) + len(con_args))
        
        st.divider()
        
        # Argument evolution
        st.markdown("### Argument Evolution")
        
        for round_num in range(1, len(pro_args) + 1):
            st.markdown(f"**Round {round_num}**")
            col1, col2 = st.columns(2)
            
            pro = next((a for a in pro_args if a.round == round_num), None)
            con = next((a for a in con_args if a.round == round_num), None)
            
            with col1:
                if pro:
                    st.markdown(f"🟢 {pro.main_point[:100]}...")
            with col2:
                if con:
                    st.markdown(f"🔴 {con.main_point[:100]}...")
    
    with tab4:
        st.markdown("## Pipeline Metrics")
        
        meta = st.session_state.metadata
        
        total_tokens = meta["total_input"] + meta["total_output"]
        cost = (meta["total_input"] * 0.000003) + (meta["total_output"] * 0.000015)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Input Tokens", meta["total_input"])
        with col2:
            st.metric("Output Tokens", meta["total_output"])
        with col3:
            st.metric("Est. Cost", f"${cost:.4f}")
        
        st.divider()
        
        st.markdown("### API Calls Breakdown")
        st.markdown(f"""
        - **Pro Agent:** {st.session_state.num_rounds} calls
        - **Con Agent:** {st.session_state.num_rounds} calls
        - **Synthesizer:** 1 call
        - **Total Calls:** {st.session_state.num_rounds * 2 + 1}
        """)
    
    # Reset button
    st.divider()
    if st.button("🔄 Start New Debate", type="primary"):
        st.session_state.stage = "input"
        st.session_state.topic = ""
        st.session_state.current_round = 0
        st.session_state.arguments = []
        st.session_state.synthesis = None
        st.session_state.metadata = {"total_input": 0, "total_output": 0}
        st.rerun()
