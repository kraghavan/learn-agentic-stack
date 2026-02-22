"""
Google Calendar API Wrapper
Handles OAuth authentication and calendar operations.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes for Google Calendar API
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
]

# Paths
CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent / "token.pickle"


class GoogleCalendarClient:
    """Client for Google Calendar API operations."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API.
        Returns True if successful.
        """
        creds = None
        
        # Load existing token
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            
            if not creds:
                if not CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"credentials.json not found at {CREDENTIALS_FILE}. "
                        "Download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )
                creds = flow.run_local_server(port=8090)
            
            # Save token for next time
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        self.service = build('calendar', 'v3', credentials=creds)
        return True
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self.service is not None
    
    def get_calendars(self) -> list[dict]:
        """Get list of user's calendars."""
        if not self.is_authenticated():
            self.authenticate()
        
        calendars = []
        page_token = None
        
        while True:
            calendar_list = self.service.calendarList().list(
                pageToken=page_token
            ).execute()
            
            for calendar in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar['id'],
                    'name': calendar.get('summary', 'Unnamed'),
                    'primary': calendar.get('primary', False),
                    'color': calendar.get('backgroundColor', '#4285f4'),
                })
            
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        
        return calendars
    
    def get_events(
        self,
        calendar_id: str = 'primary',
        time_min: datetime = None,
        time_max: datetime = None,
        max_results: int = 50,
        query: str = None
    ) -> list[dict]:
        """
        Get events from a calendar.
        
        Args:
            calendar_id: Calendar ID (default: primary)
            time_min: Start of time range (default: now)
            time_max: End of time range (default: 7 days from now)
            max_results: Maximum number of events
            query: Search query
        """
        if not self.is_authenticated():
            self.authenticate()
        
        if time_min is None:
            time_min = datetime.utcnow()
        if time_max is None:
            time_max = time_min + timedelta(days=7)
        
        # Convert to RFC3339 format
        time_min_str = time_min.isoformat() + 'Z'
        time_max_str = time_max.isoformat() + 'Z'
        
        try:
            kwargs = {
                'calendarId': calendar_id,
                'timeMin': time_min_str,
                'timeMax': time_max_str,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime',
            }
            
            if query:
                kwargs['q'] = query
            
            events_result = self.service.events().list(**kwargs).execute()
            events = events_result.get('items', [])
            
            return [self._parse_event(e) for e in events]
        
        except HttpError as e:
            raise Exception(f"Error fetching events: {e}")
    
    def get_events_today(self, calendar_id: str = 'primary') -> list[dict]:
        """Get today's events."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return self.get_events(calendar_id, time_min=today, time_max=tomorrow)
    
    def get_events_week(self, calendar_id: str = 'primary') -> list[dict]:
        """Get this week's events."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = today + timedelta(days=7)
        return self.get_events(calendar_id, time_min=today, time_max=week_end)
    
    def get_events_month(self, calendar_id: str = 'primary') -> list[dict]:
        """Get this month's events."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        month_end = today + timedelta(days=30)
        return self.get_events(calendar_id, time_min=today, time_max=month_end)
    
    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime = None,
        description: str = None,
        location: str = None,
        attendees: list[str] = None,
        calendar_id: str = 'primary',
        send_notifications: bool = True
    ) -> dict:
        """
        Create a new calendar event.
        
        Args:
            summary: Event title
            start_time: Event start datetime
            end_time: Event end datetime (default: start + 1 hour)
            description: Event description
            location: Event location
            attendees: List of email addresses
            calendar_id: Calendar ID
            send_notifications: Send email invites to attendees
        """
        if not self.is_authenticated():
            self.authenticate()
        
        if end_time is None:
            end_time = start_time + timedelta(hours=1)
        
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Los_Angeles',  # Adjust as needed
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
        }
        
        if description:
            event['description'] = description
        
        if location:
            event['location'] = location
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        try:
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendNotifications=send_notifications
            ).execute()
            
            return self._parse_event(created_event)
        
        except HttpError as e:
            raise Exception(f"Error creating event: {e}")
    
    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """Delete an event."""
        if not self.is_authenticated():
            self.authenticate()
        
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return True
        except HttpError as e:
            raise Exception(f"Error deleting event: {e}")
    
    def find_free_slots(
        self,
        duration_minutes: int = 60,
        time_min: datetime = None,
        time_max: datetime = None,
        calendar_id: str = 'primary',
        working_hours: tuple = (9, 17)
    ) -> list[dict]:
        """
        Find free time slots in the calendar.
        
        Args:
            duration_minutes: Required duration for the slot
            time_min: Start of search range
            time_max: End of search range
            calendar_id: Calendar to check
            working_hours: Tuple of (start_hour, end_hour)
        """
        if not self.is_authenticated():
            self.authenticate()
        
        if time_min is None:
            time_min = datetime.utcnow()
        if time_max is None:
            time_max = time_min + timedelta(days=7)
        
        # Get existing events
        events = self.get_events(calendar_id, time_min, time_max, max_results=100)
        
        # Build list of busy periods
        busy_periods = []
        for event in events:
            start = event.get('start_datetime')
            end = event.get('end_datetime')
            if start and end:
                busy_periods.append((start, end))
        
        # Sort by start time
        busy_periods.sort(key=lambda x: x[0])
        
        # Find free slots
        free_slots = []
        current = time_min
        
        while current < time_max:
            # Check if within working hours
            if current.hour < working_hours[0]:
                current = current.replace(hour=working_hours[0], minute=0)
            elif current.hour >= working_hours[1]:
                # Move to next day
                current = (current + timedelta(days=1)).replace(
                    hour=working_hours[0], minute=0
                )
                continue
            
            # Skip weekends
            if current.weekday() >= 5:
                current = current + timedelta(days=1)
                continue
            
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Check if slot is within working hours
            if slot_end.hour > working_hours[1]:
                current = (current + timedelta(days=1)).replace(
                    hour=working_hours[0], minute=0
                )
                continue
            
            # Check if slot conflicts with any busy period
            is_free = True
            for busy_start, busy_end in busy_periods:
                if current < busy_end and slot_end > busy_start:
                    is_free = False
                    current = busy_end
                    break
            
            if is_free:
                free_slots.append({
                    'start': current.isoformat(),
                    'end': slot_end.isoformat(),
                    'duration_minutes': duration_minutes,
                })
                current = slot_end
            
            # Limit results
            if len(free_slots) >= 10:
                break
        
        return free_slots
    
    def _parse_event(self, event: dict) -> dict:
        """Parse a Google Calendar event into a simpler format."""
        start = event.get('start', {})
        end = event.get('end', {})
        
        # Handle all-day events vs timed events
        start_str = start.get('dateTime', start.get('date', ''))
        end_str = end.get('dateTime', end.get('date', ''))
        
        # Parse datetimes
        start_dt = None
        end_dt = None
        is_all_day = 'date' in start
        
        try:
            if is_all_day:
                start_dt = datetime.fromisoformat(start_str)
                end_dt = datetime.fromisoformat(end_str)
            else:
                # Remove timezone suffix for parsing
                start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        except:
            pass
        
        return {
            'id': event.get('id', ''),
            'summary': event.get('summary', 'No Title'),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'start': start_str,
            'end': end_str,
            'start_datetime': start_dt,
            'end_datetime': end_dt,
            'is_all_day': is_all_day,
            'attendees': [
                a.get('email', '') 
                for a in event.get('attendees', [])
            ],
            'html_link': event.get('htmlLink', ''),
            'status': event.get('status', ''),
        }


# Singleton instance
_client = None

def get_client() -> GoogleCalendarClient:
    """Get or create the calendar client singleton."""
    global _client
    if _client is None:
        _client = GoogleCalendarClient()
    return _client


if __name__ == "__main__":
    # Test
    client = get_client()
    client.authenticate()
    
    print("Calendars:")
    for cal in client.get_calendars():
        print(f"  - {cal['name']} ({'Primary' if cal['primary'] else cal['id']})")
    
    print("\nToday's events:")
    for event in client.get_events_today():
        print(f"  - {event['summary']} at {event['start']}")
