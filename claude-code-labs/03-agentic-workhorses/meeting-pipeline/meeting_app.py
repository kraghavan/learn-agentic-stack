"""
Meeting Pipeline UI - Project 4.3
Streamlit interface for meeting processing and action extraction.
"""

import os
import tempfile
import streamlit as st
from datetime import datetime

from meeting_processor import (
    MeetingProcessor, MeetingSummary, ActionItem, 
    Priority, ActionType, SAMPLE_TRANSCRIPTS
)
from meeting_integrations import (
    IntegrationHub, JiraTicket, Email, CalendarEvent
)


# ============== PAGE CONFIG ==============

st.set_page_config(
    page_title="Meeting Pipeline",
    page_icon="📋",
    layout="wide"
)

# ============== SESSION STATE ==============

if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "summary" not in st.session_state:
    st.session_state.summary = None
if "integrations_result" not in st.session_state:
    st.session_state.integrations_result = None

# ============== SIDEBAR ==============

with st.sidebar:
    st.title("📋 Meeting Pipeline")
    st.markdown("---")
    
    # Pipeline stages
    stages = ["📥 Input", "📝 Transcript", "📊 Analysis", "🎯 Actions", "✅ Complete"]
    stage_map = {"input": 0, "transcript": 1, "analysis": 2, "actions": 3, "complete": 4}
    current_idx = stage_map.get(st.session_state.stage, 0)
    
    for i, stage in enumerate(stages):
        if i < current_idx:
            st.markdown(f"~~{stage}~~ ✓")
        elif i == current_idx:
            st.markdown(f"**→ {stage}**")
        else:
            st.markdown(f"{stage}")
    
    st.markdown("---")
    
    # Pipeline visualization
    st.markdown("### Pipeline")
    st.markdown("""
    ```
    Audio/Text
        │
        ▼
    📝 Transcribe
        │
        ▼
    📊 Summarize
        │
        ▼
    🎯 Extract Actions
        │
    ┌───┴───┐
    ▼       ▼
    🎫      📧
    Jira   Email
    ```
    """)
    
    st.markdown("---")
    
    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.stage = "input"
        st.session_state.transcript = ""
        st.session_state.summary = None
        st.session_state.integrations_result = None
        st.rerun()

# ============== MAIN CONTENT ==============

st.title("📋 Meeting Notes → Action Items")
st.markdown("*End-to-end meeting processing pipeline*")

# ============== STAGE: INPUT ==============

if st.session_state.stage == "input":
    st.markdown("### Upload Meeting")
    
    tab1, tab2, tab3 = st.tabs(["📄 Paste Transcript", "🎤 Upload Audio", "📝 Sample"])
    
    with tab1:
        st.markdown("Paste your meeting transcript or notes:")
        transcript = st.text_area(
            "Transcript",
            height=300,
            placeholder="Paste meeting transcript here...\n\nExample:\nJohn: Let's discuss the project timeline...\nSarah: I'll have the designs ready by Friday..."
        )
        
        if transcript:
            st.session_state.transcript = transcript
    
    with tab2:
        st.markdown("Upload an audio file (requires OpenAI API key):")
        
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Required for Whisper transcription"
        )
        
        audio_file = st.file_uploader(
            "Audio File",
            type=["mp3", "wav", "m4a", "webm"],
            help="Supported formats: MP3, WAV, M4A, WebM"
        )
        
        use_mock = st.checkbox("Use mock transcription (for testing)", value=True)
        
        if audio_file:
            st.audio(audio_file)
            
            if st.button("🎤 Transcribe"):
                if use_mock:
                    processor = MeetingProcessor()
                    transcript, _ = processor.transcriber.transcribe_mock("")
                    st.session_state.transcript = transcript
                    st.session_state.stage = "transcript"
                    st.rerun()
                elif openai_key:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        tmp.write(audio_file.getvalue())
                        tmp_path = tmp.name
                    
                    try:
                        processor = MeetingProcessor(openai_api_key=openai_key)
                        transcript, _ = processor.transcriber.transcribe(tmp_path)
                        st.session_state.transcript = transcript
                        st.session_state.stage = "transcript"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Transcription failed: {e}")
                    finally:
                        os.unlink(tmp_path)
                else:
                    st.error("Please provide OpenAI API key or enable mock transcription")
    
    with tab3:
        st.markdown("Use a sample transcript:")
        
        for name, transcript in SAMPLE_TRANSCRIPTS.items():
            if st.button(f"📝 {name.replace('_', ' ').title()}", use_container_width=True):
                st.session_state.transcript = transcript.strip()
                st.session_state.stage = "transcript"
                st.rerun()
    
    # Continue button
    if st.session_state.transcript:
        st.divider()
        if st.button("➡️ Continue to Transcript", type="primary", use_container_width=True):
            st.session_state.stage = "transcript"
            st.rerun()

# ============== STAGE: TRANSCRIPT ==============

elif st.session_state.stage == "transcript":
    st.markdown("### 📝 Review Transcript")
    
    # Meeting metadata
    col1, col2 = st.columns(2)
    with col1:
        meeting_date = st.date_input("Meeting Date", value=datetime.now())
    with col2:
        meeting_title = st.text_input("Meeting Title (optional)", placeholder="Weekly Sync")
    
    # Transcript editor
    transcript = st.text_area(
        "Transcript",
        value=st.session_state.transcript,
        height=400
    )
    st.session_state.transcript = transcript
    
    # Word count
    word_count = len(transcript.split())
    st.caption(f"📊 {word_count} words | ~{word_count // 150} minute meeting")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.stage = "input"
            st.rerun()
    with col2:
        if st.button("🔍 Analyze Meeting", type="primary", use_container_width=True):
            st.session_state.meeting_date = meeting_date.strftime("%Y-%m-%d")
            st.session_state.meeting_title = meeting_title
            st.session_state.stage = "analysis"
            st.rerun()

# ============== STAGE: ANALYSIS ==============

elif st.session_state.stage == "analysis":
    st.markdown("### 📊 Analyzing Meeting")
    
    if st.session_state.summary is None:
        with st.spinner("🧠 AI is analyzing the transcript..."):
            processor = MeetingProcessor()
            summary = processor.process_transcript(
                st.session_state.transcript,
                st.session_state.meeting_date
            )
            
            # Override title if provided
            if hasattr(st.session_state, 'meeting_title') and st.session_state.meeting_title:
                summary.title = st.session_state.meeting_title
            
            st.session_state.summary = summary
            st.rerun()
    
    summary = st.session_state.summary
    
    # Meeting header
    st.markdown(f"## {summary.title}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📅 Date", summary.date)
    with col2:
        st.metric("⏱️ Duration", f"~{summary.duration_minutes} min")
    with col3:
        st.metric("🎯 Actions", len(summary.action_items))
    
    # Attendees
    st.markdown(f"**👥 Attendees:** {', '.join(summary.attendees)}")
    
    st.divider()
    
    # Summary
    st.markdown("### 📝 Summary")
    st.info(summary.summary)
    
    # Key points
    if summary.key_points:
        st.markdown("### 💡 Key Points")
        for point in summary.key_points:
            st.markdown(f"• {point}")
    
    # Decisions
    if summary.decisions:
        st.markdown("### ✅ Decisions Made")
        for decision in summary.decisions:
            st.markdown(f"• {decision}")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Transcript", use_container_width=True):
            st.session_state.summary = None
            st.session_state.stage = "transcript"
            st.rerun()
    with col2:
        if st.button("🎯 View Action Items", type="primary", use_container_width=True):
            st.session_state.stage = "actions"
            st.rerun()

# ============== STAGE: ACTIONS ==============

elif st.session_state.stage == "actions":
    st.markdown("### 🎯 Action Items")
    
    summary = st.session_state.summary
    
    if not summary.action_items:
        st.warning("No action items were extracted from this meeting.")
    else:
        # Priority filter
        priorities = ["All"] + [p.value.title() for p in Priority]
        selected_priority = st.selectbox("Filter by Priority", priorities)
        
        # Display action items
        for i, action in enumerate(summary.action_items):
            if selected_priority != "All" and action.priority.value.title() != selected_priority:
                continue
            
            # Priority badge
            priority_colors = {
                Priority.HIGH: "🔴",
                Priority.MEDIUM: "🟡",
                Priority.LOW: "🟢"
            }
            badge = priority_colors.get(action.priority, "⚪")
            
            with st.expander(f"{badge} {action.title}", expanded=(i < 3)):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Description:** {action.description}")
                    if action.context:
                        st.markdown(f"**Context:** _{action.context}_")
                
                with col2:
                    st.markdown(f"**👤 Assignee:** {action.assignee}")
                    st.markdown(f"**📅 Due:** {action.due_date}")
                    st.markdown(f"**📌 Type:** {action.action_type.value}")
    
    st.divider()
    
    # Integration options
    st.markdown("### 🔗 Create Outputs")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        create_tickets = st.checkbox("🎫 Create Jira Tickets", value=True)
    with col2:
        create_email = st.checkbox("📧 Draft Follow-up Email", value=True)
    with col3:
        create_calendar = st.checkbox("📅 Schedule Follow-up", value=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Analysis", use_container_width=True):
            st.session_state.stage = "analysis"
            st.rerun()
    with col2:
        if st.button("🚀 Generate Outputs", type="primary", use_container_width=True):
            with st.spinner("Creating outputs..."):
                hub = IntegrationHub()
                result = hub.process_meeting_actions(
                    summary,
                    create_tickets=create_tickets,
                    send_followup=create_email,
                    schedule_followup=create_calendar
                )
                st.session_state.integrations_result = result
                st.session_state.hub = hub
            
            st.session_state.stage = "complete"
            st.rerun()

# ============== STAGE: COMPLETE ==============

elif st.session_state.stage == "complete":
    st.markdown("### ✅ Pipeline Complete!")
    st.balloons()
    
    summary = st.session_state.summary
    result = st.session_state.integrations_result
    hub = st.session_state.hub
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Action Items", len(summary.action_items))
    with col2:
        st.metric("Tickets Created", len(result.get("tickets", [])))
    with col3:
        st.metric("Emails Drafted", 1 if result.get("email") else 0)
    with col4:
        st.metric("Calendar Events", len(result.get("calendar_events", [])))
    
    st.divider()
    
    # Tabs for outputs
    tabs = st.tabs(["📋 Summary", "🎫 Jira Tickets", "📧 Email", "📅 Calendar"])
    
    with tabs[0]:
        st.markdown(f"## {summary.title}")
        st.markdown(f"**Date:** {summary.date}")
        st.markdown(f"**Attendees:** {', '.join(summary.attendees)}")
        st.markdown("---")
        st.markdown(summary.summary)
        st.markdown("---")
        st.markdown(f"**Next Steps:** {summary.next_steps}")
    
    with tabs[1]:
        if hub.jira.tickets:
            for ticket in hub.jira.list_tickets():
                with st.expander(f"🎫 {ticket.key}: {ticket.summary}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Assignee:** {ticket.assignee}")
                        st.markdown(f"**Priority:** {ticket.priority}")
                    with col2:
                        st.markdown(f"**Due:** {ticket.due_date}")
                        st.markdown(f"**Status:** {ticket.status}")
                    st.markdown("---")
                    st.markdown(ticket.description)
        else:
            st.info("No tickets were created")
    
    with tabs[2]:
        if hub.email.drafts:
            email = hub.email.drafts[0]
            st.markdown(f"**To:** {', '.join(email.to)}")
            st.markdown(f"**Subject:** {email.subject}")
            st.markdown("---")
            st.markdown(email.body)
            
            st.download_button(
                "📥 Download Email Draft",
                email.body,
                file_name="meeting_followup.txt",
                mime="text/plain"
            )
        else:
            st.info("No email was drafted")
    
    with tabs[3]:
        if hub.calendar.events:
            for event in hub.calendar.list_events():
                st.markdown(f"""
                **📅 {event.title}**
                - 🕐 {event.start} - {event.end}
                - 👥 {', '.join(event.attendees)}
                """)
                if event.description:
                    st.caption(event.description)
                st.markdown("---")
        else:
            st.info("No calendar events were created")
    
    st.divider()
    
    # Export all
    st.markdown("### 📥 Export")
    
    export_data = {
        "meeting": summary.to_dict(),
        "tickets": result.get("tickets", []),
        "email": result.get("email"),
        "calendar": result.get("calendar_events", [])
    }
    
    import json
    st.download_button(
        "📥 Download All (JSON)",
        json.dumps(export_data, indent=2),
        file_name=f"meeting_{summary.date}.json",
        mime="application/json"
    )
    
    if st.button("🔄 Process Another Meeting", use_container_width=True):
        st.session_state.stage = "input"
        st.session_state.transcript = ""
        st.session_state.summary = None
        st.session_state.integrations_result = None
        st.rerun()

# ============== FOOTER ==============

st.divider()
st.caption("📋 Meeting Pipeline | Project 4.3 | learn-agentic-stack")
