"""
Mock Integrations - Project 4.3
Simulated Jira, Email, and Calendar integrations.
"""

import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from anthropic import Anthropic

from meeting_processor import ActionItem, MeetingSummary, Priority


# ============== JIRA INTEGRATION ==============

@dataclass
class JiraTicket:
    """A Jira ticket."""
    key: str
    project: str
    summary: str
    description: str
    assignee: str
    priority: str
    due_date: str
    status: str = "To Do"
    labels: list[str] = field(default_factory=list)
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "project": self.project,
            "summary": self.summary,
            "description": self.description,
            "assignee": self.assignee,
            "priority": self.priority,
            "due_date": self.due_date,
            "status": self.status,
            "labels": self.labels,
            "created_at": self.created_at
        }
    
    def to_jira_format(self) -> str:
        """Format as Jira-like display."""
        return f"""
┌─────────────────────────────────────────────────────────────┐
│ {self.key}                                                  
├─────────────────────────────────────────────────────────────┤
│ Summary: {self.summary}
│ 
│ Description:
│ {self.description[:200]}{'...' if len(self.description) > 200 else ''}
│
│ Assignee: {self.assignee}
│ Priority: {self.priority}
│ Due Date: {self.due_date}
│ Status:   {self.status}
│ Labels:   {', '.join(self.labels) if self.labels else 'None'}
└─────────────────────────────────────────────────────────────┘
"""


class MockJiraClient:
    """Mock Jira API client."""
    
    def __init__(self, project_key: str = "MEET"):
        self.project_key = project_key
        self.tickets: dict[str, JiraTicket] = {}
        self.ticket_counter = 1
    
    def create_ticket(self, action: ActionItem, labels: list[str] = None) -> JiraTicket:
        """Create a Jira ticket from an action item."""
        ticket_key = f"{self.project_key}-{self.ticket_counter}"
        self.ticket_counter += 1
        
        # Map priority
        priority_map = {
            Priority.HIGH: "Highest",
            Priority.MEDIUM: "Medium",
            Priority.LOW: "Low"
        }
        
        ticket = JiraTicket(
            key=ticket_key,
            project=self.project_key,
            summary=action.title,
            description=f"{action.description}\n\n---\nFrom meeting context:\n> {action.context}",
            assignee=action.assignee,
            priority=priority_map.get(action.priority, "Medium"),
            due_date=action.due_date,
            labels=labels or ["meeting-action"]
        )
        
        self.tickets[ticket_key] = ticket
        return ticket
    
    def create_tickets_from_meeting(
        self,
        summary: MeetingSummary,
        labels: list[str] = None
    ) -> list[JiraTicket]:
        """Create tickets for all action items in a meeting."""
        tickets = []
        
        base_labels = labels or []
        meeting_label = f"meeting-{summary.date}"
        
        for action in summary.action_items:
            ticket = self.create_ticket(
                action,
                labels=base_labels + [meeting_label]
            )
            tickets.append(ticket)
        
        return tickets
    
    def get_ticket(self, key: str) -> Optional[JiraTicket]:
        """Get a ticket by key."""
        return self.tickets.get(key)
    
    def list_tickets(self) -> list[JiraTicket]:
        """List all tickets."""
        return list(self.tickets.values())
    
    def update_status(self, key: str, status: str) -> bool:
        """Update ticket status."""
        if key in self.tickets:
            self.tickets[key].status = status
            return True
        return False


# ============== EMAIL INTEGRATION ==============

@dataclass
class Email:
    """An email message."""
    to: list[str]
    cc: list[str]
    subject: str
    body: str
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "to": self.to,
            "cc": self.cc,
            "subject": self.subject,
            "body": self.body,
            "created_at": self.created_at
        }
    
    def to_email_format(self) -> str:
        """Format as email display."""
        return f"""
To: {', '.join(self.to)}
Cc: {', '.join(self.cc) if self.cc else '—'}
Subject: {self.subject}

{self.body}
"""


class EmailDrafter:
    """Draft follow-up emails using AI."""
    
    EMAIL_SYSTEM = """You are a professional email writer. Create clear, concise follow-up emails.

Guidelines:
- Be professional but friendly
- Include all action items with owners and due dates
- Keep it scannable with bullet points
- End with clear next steps

OUTPUT FORMAT:
{
    "subject": "Email subject line",
    "body": "Full email body with proper formatting"
}"""
    
    def __init__(self):
        self.client = Anthropic()
        self.drafts: list[Email] = []
    
    def draft_followup(
        self,
        summary: MeetingSummary,
        additional_notes: str = ""
    ) -> Email:
        """Draft a follow-up email for a meeting."""
        
        action_items_text = "\n".join([
            f"- {a.title} ({a.assignee}, due: {a.due_date})"
            for a in summary.action_items
        ])
        
        prompt = f"""Draft a follow-up email for this meeting:

Meeting: {summary.title}
Date: {summary.date}
Attendees: {', '.join(summary.attendees)}

Summary: {summary.summary}

Key Decisions:
{chr(10).join('- ' + d for d in summary.decisions)}

Action Items:
{action_items_text}

Next Steps: {summary.next_steps}

{f'Additional notes: {additional_notes}' if additional_notes else ''}

Create a professional follow-up email."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=self.EMAIL_SYSTEM,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text
        
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            subject = data.get("subject", f"Follow-up: {summary.title}")
            body = data.get("body", content)
        except (json.JSONDecodeError, KeyError):
            subject = f"Follow-up: {summary.title}"
            body = content
        
        email = Email(
            to=summary.attendees,
            cc=[],
            subject=subject,
            body=body
        )
        
        self.drafts.append(email)
        return email
    
    def draft_reminder(
        self,
        action: ActionItem,
        days_until_due: int = 1
    ) -> Email:
        """Draft a reminder email for an action item."""
        
        urgency = "urgent" if days_until_due <= 1 else "upcoming"
        
        email = Email(
            to=[action.assignee],
            cc=[],
            subject=f"Reminder: {action.title} - Due {action.due_date}",
            body=f"""Hi {action.assignee.split()[0]},

This is a friendly reminder about your {urgency} action item:

**{action.title}**

{action.description}

Due date: {action.due_date}

Please let me know if you need any support or if the timeline needs to be adjusted.

Best regards
"""
        )
        
        self.drafts.append(email)
        return email


# ============== CALENDAR INTEGRATION ==============

@dataclass
class CalendarEvent:
    """A calendar event."""
    id: str
    title: str
    start: str
    end: str
    attendees: list[str]
    description: str = ""
    location: str = ""
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start,
            "end": self.end,
            "attendees": self.attendees,
            "description": self.description,
            "location": self.location
        }
    
    def to_calendar_format(self) -> str:
        """Format as calendar display."""
        return f"""
📅 {self.title}
   🕐 {self.start} - {self.end}
   👥 {', '.join(self.attendees)}
   📍 {self.location or 'No location'}
"""


class MockCalendarClient:
    """Mock calendar integration."""
    
    def __init__(self):
        self.events: list[CalendarEvent] = []
        self.event_counter = 1
    
    def create_followup_meeting(
        self,
        summary: MeetingSummary,
        days_from_now: int = 7,
        duration_minutes: int = 30
    ) -> CalendarEvent:
        """Schedule a follow-up meeting."""
        
        start_date = datetime.now() + timedelta(days=days_from_now)
        # Set to 10 AM
        start_date = start_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(minutes=duration_minutes)
        
        event = CalendarEvent(
            id=f"evt_{self.event_counter}",
            title=f"Follow-up: {summary.title}",
            start=start_date.strftime("%Y-%m-%d %H:%M"),
            end=end_date.strftime("%Y-%m-%d %H:%M"),
            attendees=summary.attendees,
            description=f"Follow-up meeting to discuss:\n{summary.next_steps}"
        )
        
        self.events.append(event)
        self.event_counter += 1
        
        return event
    
    def create_deadline_reminder(
        self,
        action: ActionItem,
        reminder_days_before: int = 1
    ) -> CalendarEvent:
        """Create a calendar reminder for an action item deadline."""
        
        try:
            due = datetime.strptime(action.due_date, "%Y-%m-%d")
            reminder_date = due - timedelta(days=reminder_days_before)
        except ValueError:
            reminder_date = datetime.now() + timedelta(days=7)
        
        reminder_date = reminder_date.replace(hour=9, minute=0)
        
        event = CalendarEvent(
            id=f"evt_{self.event_counter}",
            title=f"⚠️ Due Tomorrow: {action.title}",
            start=reminder_date.strftime("%Y-%m-%d %H:%M"),
            end=(reminder_date + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M"),
            attendees=[action.assignee],
            description=f"Reminder: This task is due {action.due_date}\n\n{action.description}"
        )
        
        self.events.append(event)
        self.event_counter += 1
        
        return event
    
    def list_events(self) -> list[CalendarEvent]:
        """List all events."""
        return self.events


# ============== INTEGRATION HUB ==============

class IntegrationHub:
    """Central hub for all integrations."""
    
    def __init__(self, jira_project: str = "MEET"):
        self.jira = MockJiraClient(jira_project)
        self.email = EmailDrafter()
        self.calendar = MockCalendarClient()
    
    def process_meeting_actions(
        self,
        summary: MeetingSummary,
        create_tickets: bool = True,
        send_followup: bool = True,
        schedule_followup: bool = True
    ) -> dict:
        """
        Process a meeting through all integrations.
        
        Returns:
            Dictionary with created items
        """
        result = {
            "tickets": [],
            "email": None,
            "calendar_events": []
        }
        
        # Create Jira tickets
        if create_tickets and summary.action_items:
            tickets = self.jira.create_tickets_from_meeting(summary)
            result["tickets"] = [t.to_dict() for t in tickets]
        
        # Draft follow-up email
        if send_followup:
            email = self.email.draft_followup(summary)
            result["email"] = email.to_dict()
        
        # Schedule follow-up meeting
        if schedule_followup:
            event = self.calendar.create_followup_meeting(summary)
            result["calendar_events"].append(event.to_dict())
            
            # Add deadline reminders for high-priority items
            for action in summary.action_items:
                if action.priority == Priority.HIGH:
                    reminder = self.calendar.create_deadline_reminder(action)
                    result["calendar_events"].append(reminder.to_dict())
        
        return result


if __name__ == "__main__":
    from meeting_processor import SAMPLE_TRANSCRIPTS, MeetingProcessor
    
    # Process a meeting
    processor = MeetingProcessor()
    summary = processor.process_transcript(SAMPLE_TRANSCRIPTS["weekly_sync"])
    
    # Run through integrations
    hub = IntegrationHub()
    result = hub.process_meeting_actions(summary)
    
    print("=" * 60)
    print("JIRA TICKETS CREATED")
    print("=" * 60)
    for ticket in hub.jira.list_tickets():
        print(ticket.to_jira_format())
    
    print("\n" + "=" * 60)
    print("FOLLOW-UP EMAIL")
    print("=" * 60)
    if hub.email.drafts:
        print(hub.email.drafts[0].to_email_format())
    
    print("\n" + "=" * 60)
    print("CALENDAR EVENTS")
    print("=" * 60)
    for event in hub.calendar.list_events():
        print(event.to_calendar_format())
