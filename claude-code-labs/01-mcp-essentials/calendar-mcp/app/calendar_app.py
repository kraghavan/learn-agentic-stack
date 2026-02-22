"""
Calendar Manager UI - Project 2.2
Streamlit interface for Google Calendar integration.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from calendar_client import get_client, GoogleCalendarClient
from anthropic import Anthropic

# Initialize Claude client for natural language parsing
claude = Anthropic()


def parse_natural_language_event(text: str) -> dict:
    """Use Claude to parse natural language into event details."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""Parse this natural language event description into structured data.

Today's date is: {today}

User input: "{text}"

Return ONLY a JSON object with these fields (no explanation):
{{
    "summary": "event title",
    "start_time": "YYYY-MM-DDTHH:MM:SS",
    "end_time": "YYYY-MM-DDTHH:MM:SS",
    "description": "description or null",
    "location": "location or null",
    "attendees": ["email1@example.com"] or []
}}

If time is ambiguous, assume business hours. If duration is not specified, assume 1 hour.
If the date is relative (tomorrow, next week, etc.), calculate the actual date."""

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        result = response.content[0].text
        # Clean up response
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        return json.loads(result.strip())
    except:
        return None


# ============== STREAMLIT UI ==============

st.set_page_config(
    page_title="Calendar Manager",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Calendar Manager")
st.markdown("*Google Calendar integration with natural language scheduling*")

# Initialize session state
if "client" not in st.session_state:
    st.session_state.client = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "events" not in st.session_state:
    st.session_state.events = []

# Sidebar
with st.sidebar:
    st.header("🔐 Authentication")
    
    if not st.session_state.authenticated:
        st.warning("Not connected to Google Calendar")
        
        if st.button("🔗 Connect Google Account", type="primary", use_container_width=True):
            try:
                client = get_client()
                client.authenticate()
                st.session_state.client = client
                st.session_state.authenticated = True
                st.success("Connected!")
                st.rerun()
            except FileNotFoundError as e:
                st.error("credentials.json not found! Download it from Google Cloud Console.")
            except Exception as e:
                st.error(f"Authentication failed: {e}")
    else:
        st.success("✓ Connected to Google Calendar")
        
        # Calendar selector
        st.divider()
        st.subheader("📚 Calendars")
        
        try:
            calendars = st.session_state.client.get_calendars()
            calendar_options = {
                f"{cal['name']} {'(Primary)' if cal['primary'] else ''}": cal['id']
                for cal in calendars
            }
            selected_cal_name = st.selectbox("Select Calendar", list(calendar_options.keys()))
            st.session_state.selected_calendar = calendar_options[selected_cal_name]
        except Exception as e:
            st.error(f"Error loading calendars: {e}")
            st.session_state.selected_calendar = "primary"
        
        st.divider()
        
        # Time range
        st.subheader("📆 Time Range")
        view_option = st.radio(
            "View",
            ["Today", "This Week", "This Month", "Custom"]
        )
        
        if view_option == "Custom":
            start_date = st.date_input("From", datetime.now())
            end_date = st.date_input("To", datetime.now() + timedelta(days=7))
        
        if st.button("🔄 Refresh Events", use_container_width=True):
            try:
                client = st.session_state.client
                cal_id = st.session_state.get("selected_calendar", "primary")
                
                if view_option == "Today":
                    events = client.get_events_today(cal_id)
                elif view_option == "This Week":
                    events = client.get_events_week(cal_id)
                elif view_option == "This Month":
                    events = client.get_events_month(cal_id)
                else:
                    events = client.get_events(
                        cal_id,
                        time_min=datetime.combine(start_date, datetime.min.time()),
                        time_max=datetime.combine(end_date, datetime.max.time())
                    )
                
                st.session_state.events = events
                st.success(f"Loaded {len(events)} events")
            except Exception as e:
                st.error(f"Error: {e}")

# Main content
if not st.session_state.authenticated:
    st.info("👈 Click 'Connect Google Account' in the sidebar to get started.")
    
    st.markdown("""
    ### Setup Instructions
    
    1. **Create Google Cloud Project**
       - Go to [Google Cloud Console](https://console.cloud.google.com/)
       - Create a new project
    
    2. **Enable Calendar API**
       - Go to "APIs & Services" → "Library"
       - Search "Google Calendar API" and enable it
    
    3. **Create OAuth Credentials**
       - Go to "APIs & Services" → "Credentials"
       - Create OAuth 2.0 Client ID (Desktop app)
       - Download the JSON file
       - Rename to `credentials.json`
       - Place in the `calendar-mcp/` folder
    
    4. **Add Test User**
       - Go to "OAuth consent screen"
       - Add your email as a test user
    
    5. **Connect**
       - Click "Connect Google Account" above
       - A browser window will open for authorization
    """)

else:
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Events", "➕ Create Event", "🔍 Find Free Time", "💬 Natural Language"])
    
    with tab1:
        st.subheader("Your Events")
        
        events = st.session_state.events
        
        if not events:
            st.info("No events found. Click 'Refresh Events' in the sidebar.")
        else:
            for event in events:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{event['summary']}**")
                        if event.get('location'):
                            st.caption(f"📍 {event['location']}")
                    
                    with col2:
                        if event['is_all_day']:
                            st.write("🗓️ All Day")
                        else:
                            start = event['start'][:16].replace('T', ' ')
                            st.write(f"🕐 {start}")
                    
                    with col3:
                        if st.button("🗑️", key=f"del_{event['id']}", help="Delete event"):
                            try:
                                st.session_state.client.delete_event(
                                    event['id'],
                                    st.session_state.get("selected_calendar", "primary")
                                )
                                st.success("Deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    
                    if event.get('description'):
                        with st.expander("Description"):
                            st.write(event['description'])
                    
                    if event.get('attendees'):
                        with st.expander(f"Attendees ({len(event['attendees'])})"):
                            for attendee in event['attendees']:
                                st.write(f"• {attendee}")
                    
                    st.divider()
    
    with tab2:
        st.subheader("Create New Event")
        
        with st.form("create_event_form"):
            summary = st.text_input("Event Title*", placeholder="Team Meeting")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", datetime.now())
                start_time = st.time_input("Start Time", datetime.now().replace(hour=9, minute=0))
            with col2:
                end_date = st.date_input("End Date", datetime.now())
                end_time = st.time_input("End Time", datetime.now().replace(hour=10, minute=0))
            
            location = st.text_input("Location", placeholder="Conference Room A")
            description = st.text_area("Description", placeholder="Meeting agenda...")
            attendees_input = st.text_input("Attendees (comma-separated emails)", placeholder="alice@example.com, bob@example.com")
            
            submitted = st.form_submit_button("Create Event", type="primary")
            
            if submitted:
                if not summary:
                    st.error("Event title is required")
                else:
                    try:
                        start_dt = datetime.combine(start_date, start_time)
                        end_dt = datetime.combine(end_date, end_time)
                        
                        attendees = [a.strip() for a in attendees_input.split(",") if a.strip()] if attendees_input else None
                        
                        event = st.session_state.client.create_event(
                            summary=summary,
                            start_time=start_dt,
                            end_time=end_dt,
                            description=description if description else None,
                            location=location if location else None,
                            attendees=attendees,
                            calendar_id=st.session_state.get("selected_calendar", "primary")
                        )
                        
                        st.success(f"Event created: {event['summary']}")
                        st.markdown(f"[Open in Google Calendar]({event['html_link']})")
                    except Exception as e:
                        st.error(f"Error creating event: {e}")
    
    with tab3:
        st.subheader("Find Available Time Slots")
        
        col1, col2 = st.columns(2)
        
        with col1:
            duration = st.slider("Meeting Duration (minutes)", 15, 120, 60, 15)
        with col2:
            days_ahead = st.slider("Search Days Ahead", 1, 14, 7)
        
        if st.button("🔍 Find Free Slots", type="primary"):
            try:
                slots = st.session_state.client.find_free_slots(
                    duration_minutes=duration,
                    time_max=datetime.utcnow() + timedelta(days=days_ahead),
                    calendar_id=st.session_state.get("selected_calendar", "primary")
                )
                
                if slots:
                    st.success(f"Found {len(slots)} available slots")
                    
                    for i, slot in enumerate(slots):
                        start = slot['start'][:16].replace('T', ' ')
                        end = slot['end'][11:16]
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"📅 {start} - {end}")
                        with col2:
                            if st.button("Book", key=f"book_{i}"):
                                st.session_state.prefill_start = slot['start']
                                st.session_state.prefill_end = slot['end']
                                st.info("Go to 'Create Event' tab to complete booking")
                else:
                    st.warning("No free slots found in the specified time range")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with tab4:
        st.subheader("Natural Language Event Creation")
        st.caption("Describe your event in plain English and Claude will parse it")
        
        nl_input = st.text_area(
            "Describe your event",
            placeholder="Schedule a meeting with john@example.com tomorrow at 2pm for 30 minutes to discuss the project roadmap",
            height=100
        )
        
        if st.button("🤖 Parse & Preview", type="primary"):
            if nl_input:
                with st.spinner("Claude is parsing..."):
                    parsed = parse_natural_language_event(nl_input)
                
                if parsed:
                    st.session_state.parsed_event = parsed
                    st.success("Parsed successfully!")
                else:
                    st.error("Could not parse the event description. Try being more specific.")
        
        if "parsed_event" in st.session_state:
            st.divider()
            st.subheader("Parsed Event")
            
            parsed = st.session_state.parsed_event
            
            st.json(parsed)
            
            if st.button("✅ Create This Event", type="primary"):
                try:
                    start_time = datetime.fromisoformat(parsed["start_time"])
                    end_time = datetime.fromisoformat(parsed["end_time"]) if parsed.get("end_time") else None
                    
                    event = st.session_state.client.create_event(
                        summary=parsed["summary"],
                        start_time=start_time,
                        end_time=end_time,
                        description=parsed.get("description"),
                        location=parsed.get("location"),
                        attendees=parsed.get("attendees"),
                        calendar_id=st.session_state.get("selected_calendar", "primary")
                    )
                    
                    st.success(f"Event created: {event['summary']}")
                    st.markdown(f"[Open in Google Calendar]({event['html_link']})")
                    del st.session_state.parsed_event
                except Exception as e:
                    st.error(f"Error: {e}")

# Footer
st.divider()
st.caption("Project 2.2 - Calendar MCP Server | learn-agentic-stack")
