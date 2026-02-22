"""
Code Review Pipeline UI - Project 3.2
Streamlit interface for the three-agent code review system.
"""

import streamlit as st
import time
from review_orchestrator import (
    run_analyzer, run_security_scanner, run_reviewer,
    AnalyzerFindings, SecurityFindings, CodeReview,
    SAMPLE_CODE
)


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="Code Review Pipeline",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Code Review Pipeline")
st.markdown("*Three-agent system: Analyzer → Security Scanner → Review Writer*")

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "analyzer_findings" not in st.session_state:
    st.session_state.analyzer_findings = None
if "security_findings" not in st.session_state:
    st.session_state.security_findings = None
if "review" not in st.session_state:
    st.session_state.review = None
if "metadata" not in st.session_state:
    st.session_state.metadata = {}
if "code" not in st.session_state:
    st.session_state.code = ""

# Pipeline visualization
st.markdown("### Pipeline")

col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 0.5, 2, 0.5, 2, 0.5, 2])

stage = st.session_state.stage

with col1:
    if stage == "input":
        st.info("📄 **Code**\nWaiting...")
    else:
        st.success("📄 **Code**\n✓ Submitted")

with col2:
    st.markdown("<div style='text-align: center; padding-top: 20px;'>→</div>", unsafe_allow_html=True)

with col3:
    if stage == "input":
        st.warning("🔬 **Analyzer**\nIdle")
    elif stage == "analyzing":
        st.info("🔬 **Analyzer**\n⏳ Working...")
    else:
        st.success("🔬 **Analyzer**\n✓ Done")

with col4:
    st.markdown("<div style='text-align: center; padding-top: 20px;'>→</div>", unsafe_allow_html=True)

with col5:
    if stage in ["input", "analyzing"]:
        st.warning("🛡️ **Security**\nIdle")
    elif stage == "scanning":
        st.info("🛡️ **Security**\n⏳ Scanning...")
    else:
        st.success("🛡️ **Security**\n✓ Done")

with col6:
    st.markdown("<div style='text-align: center; padding-top: 20px;'>→</div>", unsafe_allow_html=True)

with col7:
    if stage in ["input", "analyzing", "scanning"]:
        st.warning("✍️ **Reviewer**\nIdle")
    elif stage == "reviewing":
        st.info("✍️ **Reviewer**\n⏳ Writing...")
    else:
        st.success("✍️ **Reviewer**\n✓ Done")

st.divider()

# Input stage
if st.session_state.stage == "input":
    st.markdown("### Submit Code for Review")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        file_name = st.text_input("File Name", value="code.py")
    
    with col2:
        if st.button("📋 Load Sample", help="Load sample code with issues"):
            st.session_state.code = SAMPLE_CODE
            st.rerun()
    
    code = st.text_area(
        "Code to Review",
        value=st.session_state.code,
        height=400,
        placeholder="Paste your code here..."
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚀 Start Review", type="primary", disabled=not code):
            st.session_state.code = code
            st.session_state.file_name = file_name
            st.session_state.stage = "analyzing"
            st.rerun()

# Analyzing stage
elif st.session_state.stage == "analyzing":
    st.markdown("### 🔬 Code Analyzer Working...")
    
    with st.spinner("Analyzing code quality, logic, and patterns..."):
        start_time = time.time()
        analyzer_findings, metadata = run_analyzer(
            st.session_state.code,
            st.session_state.file_name
        )
        elapsed = time.time() - start_time
    
    st.session_state.analyzer_findings = analyzer_findings
    st.session_state.metadata["analyzer"] = {**metadata, "elapsed": round(elapsed, 2)}
    st.session_state.stage = "scanning"
    st.rerun()

# Security scanning stage
elif st.session_state.stage == "scanning":
    st.markdown("### 🛡️ Security Scanner Working...")
    
    # Show analyzer results while scanning
    with st.expander("🔬 Analyzer Findings", expanded=True):
        af = st.session_state.analyzer_findings
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Complexity", f"{af.complexity_score}/10")
        with col2:
            st.metric("Maintainability", f"{af.maintainability_score}/10")
        st.caption(f"Found {len(af.logic_issues)} logic issues, {len(af.code_smells)} code smells")
    
    with st.spinner("Scanning for security vulnerabilities..."):
        start_time = time.time()
        security_findings, metadata = run_security_scanner(
            st.session_state.code,
            st.session_state.file_name
        )
        elapsed = time.time() - start_time
    
    st.session_state.security_findings = security_findings
    st.session_state.metadata["security"] = {**metadata, "elapsed": round(elapsed, 2)}
    st.session_state.stage = "reviewing"
    st.rerun()

# Review writing stage
elif st.session_state.stage == "reviewing":
    st.markdown("### ✍️ Review Writer Working...")
    
    # Show both findings
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("🔬 Analyzer Findings", expanded=True):
            af = st.session_state.analyzer_findings
            st.metric("Quality Score", f"{(af.complexity_score + af.maintainability_score) // 2}/10")
            st.caption(f"{len(af.logic_issues)} issues, {len(af.code_smells)} smells")
    
    with col2:
        with st.expander("🛡️ Security Findings", expanded=True):
            sf = st.session_state.security_findings
            st.metric("Security Score", f"{sf.security_score}/10")
            st.caption(f"🔴 {sf.critical_count} critical, 🟠 {sf.high_count} high")
    
    with st.spinner("Synthesizing findings into review..."):
        start_time = time.time()
        review, metadata = run_reviewer(
            st.session_state.code,
            st.session_state.analyzer_findings,
            st.session_state.security_findings,
            st.session_state.file_name
        )
        elapsed = time.time() - start_time
    
    st.session_state.review = review
    st.session_state.metadata["reviewer"] = {**metadata, "elapsed": round(elapsed, 2)}
    st.session_state.stage = "complete"
    st.rerun()

# Complete - show results
elif st.session_state.stage == "complete":
    
    review = st.session_state.review
    
    # Summary banner
    rec_colors = {
        "approve": "🟢",
        "request_changes": "🟡", 
        "needs_discussion": "🟠"
    }
    rec_icon = rec_colors.get(review.recommendation, "⚪")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Score", f"{review.overall_score}/10")
    with col2:
        st.metric("Recommendation", f"{rec_icon} {review.recommendation.replace('_', ' ').title()}")
    with col3:
        st.metric("Action Items", len(review.action_items))
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Full Review", 
        "💬 Inline Comments", 
        "🔬 Analysis", 
        "🛡️ Security",
        "📊 Metrics"
    ])
    
    with tab1:
        st.markdown(review.full_review)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ✅ Action Items")
            for item in review.action_items:
                st.markdown(f"- [ ] {item}")
        
        with col2:
            st.markdown("#### 👍 Positive Feedback")
            for item in review.positive_feedback:
                st.markdown(f"- {item}")
    
    with tab2:
        st.markdown("### Code with Inline Comments")
        
        # Build a simple code view with comments
        code_lines = st.session_state.code.split('\n')
        comments_by_line = {}
        for comment in review.inline_comments:
            line = comment.get("line", 0)
            if line not in comments_by_line:
                comments_by_line[line] = []
            comments_by_line[line].append(comment)
        
        # Display code with comments
        for i, line in enumerate(code_lines, 1):
            # Show the code line
            st.code(f"{i:3} | {line}", language=None)
            
            # Show any comments for this line
            if i in comments_by_line:
                for comment in comments_by_line[i]:
                    comment_type = comment.get("type", "info")
                    icons = {
                        "issue": "⚠️",
                        "security": "🛡️",
                        "suggestion": "💡",
                        "praise": "👍",
                        "question": "❓"
                    }
                    icon = icons.get(comment_type, "💬")
                    
                    if comment_type == "security":
                        st.error(f"{icon} {comment.get('comment', '')}")
                    elif comment_type == "issue":
                        st.warning(f"{icon} {comment.get('comment', '')}")
                    elif comment_type == "praise":
                        st.success(f"{icon} {comment.get('comment', '')}")
                    else:
                        st.info(f"{icon} {comment.get('comment', '')}")
    
    with tab3:
        af = st.session_state.analyzer_findings
        
        st.markdown(f"### {af.file_name}")
        st.markdown(f"**Language:** {af.language}")
        st.markdown(f"**Summary:** {af.summary}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Complexity Score", f"{af.complexity_score}/10")
        with col2:
            st.metric("Maintainability", f"{af.maintainability_score}/10")
        
        st.divider()
        
        if af.logic_issues:
            st.markdown("#### 🐛 Logic Issues")
            for issue in af.logic_issues:
                severity = issue.get("severity", "medium")
                sev_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                st.markdown(f"{sev_colors.get(severity, '⚪')} **Line {issue.get('line', '?')}**: {issue.get('issue', '')}")
                st.caption(f"💡 {issue.get('suggestion', '')}")
        
        if af.code_smells:
            st.markdown("#### 🦨 Code Smells")
            for smell in af.code_smells:
                st.markdown(f"- **Line {smell.get('line', '?')}**: {smell.get('issue', '')}")
        
        if af.best_practices:
            st.markdown("#### 📚 Best Practice Suggestions")
            for bp in af.best_practices:
                st.markdown(f"- **Line {bp.get('line', '?')}**: {bp.get('issue', '')}")
    
    with tab4:
        sf = st.session_state.security_findings
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔴 Critical", sf.critical_count)
        with col2:
            st.metric("🟠 High", sf.high_count)
        with col3:
            st.metric("🟡 Medium", sf.medium_count)
        with col4:
            st.metric("🟢 Low", sf.low_count)
        
        st.metric("Security Score", f"{sf.security_score}/10")
        
        st.divider()
        
        if sf.vulnerabilities:
            st.markdown("#### 🚨 Vulnerabilities")
            for vuln in sf.vulnerabilities:
                severity = vuln.get("severity", "medium")
                sev_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                
                with st.expander(f"{sev_colors.get(severity, '⚪')} Line {vuln.get('line', '?')}: {vuln.get('issue', '')}"):
                    st.markdown(f"**CWE:** {vuln.get('cwe', 'N/A')}")
                    st.markdown(f"**Fix:** {vuln.get('fix', 'No fix provided')}")
        
        if sf.sensitive_data:
            st.markdown("#### 🔐 Sensitive Data Exposure")
            for data in sf.sensitive_data:
                st.warning(f"Line {data.get('line', '?')}: {data.get('issue', '')} ({data.get('type', 'unknown')})")
        
        if sf.dependency_issues:
            st.markdown("#### 📦 Dependency Issues")
            for issue in sf.dependency_issues:
                st.markdown(f"- {issue}")
    
    with tab5:
        st.markdown("### Pipeline Metrics")
        
        meta = st.session_state.metadata
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🔬 Analyzer")
            if "analyzer" in meta:
                st.metric("Tokens", f"{meta['analyzer']['input_tokens']} in / {meta['analyzer']['output_tokens']} out")
                st.metric("Time", f"{meta['analyzer']['elapsed']}s")
        
        with col2:
            st.markdown("#### 🛡️ Security")
            if "security" in meta:
                st.metric("Tokens", f"{meta['security']['input_tokens']} in / {meta['security']['output_tokens']} out")
                st.metric("Time", f"{meta['security']['elapsed']}s")
        
        with col3:
            st.markdown("#### ✍️ Reviewer")
            if "reviewer" in meta:
                st.metric("Tokens", f"{meta['reviewer']['input_tokens']} in / {meta['reviewer']['output_tokens']} out")
                st.metric("Time", f"{meta['reviewer']['elapsed']}s")
        
        st.divider()
        
        # Totals
        total_in = sum(m.get("input_tokens", 0) for m in meta.values())
        total_out = sum(m.get("output_tokens", 0) for m in meta.values())
        total_time = sum(m.get("elapsed", 0) for m in meta.values())
        cost = (total_in * 0.000003) + (total_out * 0.000015)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Input", total_in)
        with col2:
            st.metric("Total Output", total_out)
        with col3:
            st.metric("Total Time", f"{total_time:.1f}s")
        with col4:
            st.metric("Est. Cost", f"${cost:.4f}")
    
    # Reset button
    st.divider()
    if st.button("🔄 Review Another File", type="primary"):
        st.session_state.stage = "input"
        st.session_state.analyzer_findings = None
        st.session_state.security_findings = None
        st.session_state.review = None
        st.session_state.metadata = {}
        st.session_state.code = ""
        st.rerun()

# Sidebar
with st.sidebar:
    st.header("📖 Pipeline Architecture")
    
    st.markdown("""
    ```
    Code Input
        │
        ▼
    ┌─────────┐
    │Analyzer │──┐
    └─────────┘  │
                 ├──▶ Reviewer
    ┌─────────┐  │
    │Security │──┘
    └─────────┘
        │
        ▼
    Final Review
    ```
    
    ### Agents
    
    **🔬 Analyzer**
    - Logic issues
    - Code smells
    - Best practices
    - Complexity scoring
    
    **🛡️ Security Scanner**
    - Vulnerabilities (CWE)
    - Sensitive data
    - Insecure patterns
    
    **✍️ Review Writer**
    - Synthesizes findings
    - Inline comments
    - Action items
    - Recommendations
    
    ### Key Concept
    
    Analyzer and Security can run **in parallel** since they don't depend on each other.
    
    Reviewer must wait for **both** to complete.
    """)
    
    st.divider()
    st.caption("Project 3.2 | learn-agentic-stack")
