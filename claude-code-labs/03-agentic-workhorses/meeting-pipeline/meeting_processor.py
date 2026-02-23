"""
Meeting Processor - Project 4.3
Transcription, summarization, and action item extraction.
"""

import os
import json
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from anthropic import Anthropic

# Optional: OpenAI for Whisper transcription
try:
    import openai
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionType(str, Enum):
    TASK = "task"
    FOLLOWUP = "followup"
    DECISION = "decision"
    QUESTION = "question"


@dataclass
class ActionItem:
    """An extracted action item."""
    id: str
    title: str
    description: str
    assignee: str
    due_date: str
    priority: Priority
    action_type: ActionType
    context: str = ""  # Quote from transcript
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "assignee": self.assignee,
            "due_date": self.due_date,
            "priority": self.priority.value,
            "action_type": self.action_type.value,
            "context": self.context
        }


@dataclass
class MeetingSummary:
    """Summary of a meeting."""
    title: str
    date: str
    duration_minutes: int
    attendees: list[str]
    summary: str
    key_points: list[str]
    decisions: list[str]
    action_items: list[ActionItem]
    next_steps: str
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "date": self.date,
            "duration_minutes": self.duration_minutes,
            "attendees": self.attendees,
            "summary": self.summary,
            "key_points": self.key_points,
            "decisions": self.decisions,
            "action_items": [a.to_dict() for a in self.action_items],
            "next_steps": self.next_steps
        }


class MeetingTranscriber:
    """Transcribe audio to text using Whisper."""
    
    def __init__(self, api_key: str = None):
        if WHISPER_AVAILABLE:
            self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        else:
            self.client = None
    
    def transcribe(self, audio_path: str) -> tuple[str, dict]:
        """
        Transcribe audio file to text.
        
        Returns:
            (transcript_text, metadata)
        """
        if not self.client:
            raise RuntimeError("OpenAI not available. Install with: pip install openai")
        
        with open(audio_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        # Extract segments with timestamps
        segments = []
        if hasattr(response, 'segments'):
            for seg in response.segments:
                segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text
                })
        
        metadata = {
            "duration": response.duration if hasattr(response, 'duration') else 0,
            "language": response.language if hasattr(response, 'language') else "en",
            "segments": segments
        }
        
        return response.text, metadata
    
    def transcribe_mock(self, audio_path: str) -> tuple[str, dict]:
        """Mock transcription for testing without API."""
        mock_transcript = """
John: Alright everyone, let's start the weekly sync. Sarah, can you give us an update on the API redesign?

Sarah: Sure. We've completed the initial design phase. The new endpoints are documented and I'll be sharing the specs with the team by Friday. We need Mike to review the authentication flow before we proceed.

Mike: I can do that. I'll have comments ready by Monday. Also, I wanted to mention that the database migration is blocked - we need DevOps to provision the new staging environment.

John: Good point. I'll follow up with DevOps today and get that sorted. Target is to have staging ready by next Wednesday.

Sarah: That works. Once staging is up, I'll need about a week for integration testing. So we're looking at end of month for the beta release.

John: Perfect. Let's also make sure we update the client documentation. Sarah, can you coordinate with the docs team?

Sarah: Will do. I'll set up a meeting with them this week.

Mike: One more thing - should we schedule a demo for stakeholders before the beta?

John: Great idea. Let's plan that for the 25th. I'll send out calendar invites. Anything else?

Sarah: I think we're good. Thanks everyone!

John: Alright, meeting adjourned. Talk to you all next week.
"""
        
        metadata = {
            "duration": 847,  # ~14 minutes
            "language": "en",
            "segments": [],
            "mock": True
        }
        
        return mock_transcript.strip(), metadata


class MeetingAnalyzer:
    """Analyze meeting transcripts using Claude."""
    
    EXTRACTION_SYSTEM = """You are a meeting analyst. Extract structured information from meeting transcripts.

For each action item, identify:
- A clear, actionable title
- Who is responsible (assignee)
- Due date (explicit or inferred)
- Priority (high/medium/low)
- Type (task/followup/decision/question)
- The relevant quote from the transcript

OUTPUT FORMAT (JSON only):
{
    "title": "Meeting title inferred from content",
    "attendees": ["Person1", "Person2"],
    "summary": "2-3 sentence summary",
    "key_points": ["Point 1", "Point 2"],
    "decisions": ["Decision made during meeting"],
    "action_items": [
        {
            "id": "action_1",
            "title": "Short action title",
            "description": "Detailed description",
            "assignee": "Person name",
            "due_date": "YYYY-MM-DD or 'TBD'",
            "priority": "high|medium|low",
            "action_type": "task|followup|decision|question",
            "context": "Exact quote from transcript"
        }
    ],
    "next_steps": "Summary of what happens next"
}

Be thorough - extract ALL action items mentioned. Infer due dates from context (e.g., "by Friday" → calculate the date)."""

    def __init__(self):
        self.client = Anthropic()
    
    def analyze(self, transcript: str, meeting_date: str = None) -> MeetingSummary:
        """
        Analyze a meeting transcript.
        
        Args:
            transcript: The meeting transcript text
            meeting_date: Date of the meeting (for calculating due dates)
        
        Returns:
            MeetingSummary with extracted information
        """
        if not meeting_date:
            meeting_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""Analyze this meeting transcript from {meeting_date}.

TRANSCRIPT:
{transcript}

Extract all information including action items with assignees and due dates.
Calculate actual dates where relative dates are mentioned (e.g., "by Friday" from a Monday meeting)."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=self.EXTRACTION_SYSTEM,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text
        
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            
            action_items = []
            for item in data.get("action_items", []):
                action_items.append(ActionItem(
                    id=item.get("id", f"action_{len(action_items)+1}"),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    assignee=item.get("assignee", "Unassigned"),
                    due_date=item.get("due_date", "TBD"),
                    priority=Priority(item.get("priority", "medium")),
                    action_type=ActionType(item.get("action_type", "task")),
                    context=item.get("context", "")
                ))
            
            # Estimate duration from transcript length
            word_count = len(transcript.split())
            estimated_duration = max(5, word_count // 150)  # ~150 words per minute
            
            return MeetingSummary(
                title=data.get("title", "Meeting"),
                date=meeting_date,
                duration_minutes=estimated_duration,
                attendees=data.get("attendees", []),
                summary=data.get("summary", ""),
                key_points=data.get("key_points", []),
                decisions=data.get("decisions", []),
                action_items=action_items,
                next_steps=data.get("next_steps", "")
            )
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Return basic summary on parse failure
            return MeetingSummary(
                title="Meeting",
                date=meeting_date,
                duration_minutes=0,
                attendees=[],
                summary=f"Analysis failed: {e}",
                key_points=[],
                decisions=[],
                action_items=[],
                next_steps=""
            )
    
    def refine_action_item(self, action: ActionItem, context: str) -> ActionItem:
        """Refine an action item with more detail."""
        prompt = f"""Refine this action item to be more specific and actionable:

Original: {action.title}
Description: {action.description}
Context: {context}

Provide a clearer title and more detailed description."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Simple refinement - just update description
        action.description = response.content[0].text
        return action


class MeetingProcessor:
    """End-to-end meeting processing pipeline."""
    
    def __init__(self, openai_api_key: str = None):
        self.transcriber = MeetingTranscriber(openai_api_key)
        self.analyzer = MeetingAnalyzer()
    
    def process_audio(
        self,
        audio_path: str,
        meeting_date: str = None,
        use_mock: bool = False
    ) -> tuple[str, MeetingSummary]:
        """
        Process an audio file through the full pipeline.
        
        Returns:
            (transcript, summary)
        """
        # Step 1: Transcribe
        if use_mock:
            transcript, meta = self.transcriber.transcribe_mock(audio_path)
        else:
            transcript, meta = self.transcriber.transcribe(audio_path)
        
        # Step 2: Analyze
        summary = self.analyzer.analyze(transcript, meeting_date)
        
        # Update duration from transcription if available
        if meta.get("duration"):
            summary.duration_minutes = int(meta["duration"] / 60)
        
        return transcript, summary
    
    def process_transcript(
        self,
        transcript: str,
        meeting_date: str = None
    ) -> MeetingSummary:
        """Process a text transcript directly."""
        return self.analyzer.analyze(transcript, meeting_date)


# Sample transcripts for testing
SAMPLE_TRANSCRIPTS = {
    "weekly_sync": """
John: Good morning everyone. Let's go through our weekly updates. Sarah, how's the frontend coming along?

Sarah: We're on track. The new dashboard is about 80% complete. I need to finish the charts component by Thursday, then we can start testing. Lisa, I'll need your help with the accessibility review.

Lisa: Sure, I can do that Friday. Also, I wanted to bring up the user feedback from last week - several users reported issues with the mobile navigation.

John: That's important. Can you create a ticket for that and prioritize it?

Lisa: Will do. I'll have it in Jira by end of day.

Mike: Quick update from backend - the API performance improvements are done. We're seeing 40% faster response times. I'll document the changes and share with the team tomorrow.

John: Excellent work Mike. Make sure to update the changelog as well.

Mike: Already on it.

John: Perfect. Any blockers anyone wants to discuss?

Sarah: Actually yes - I'm blocked on the design specs for the settings page. Tom, any update?

Tom: Sorry about that. I'll have the final mockups to you by Wednesday morning.

John: Great. Let's wrap up. Action items: Sarah finishes charts by Thursday, Lisa does accessibility review Friday and creates the mobile nav ticket, Mike documents API changes tomorrow, and Tom delivers settings mockups by Wednesday. Everyone clear?

All: Yes.

John: See you all next week!
""",
    
    "sprint_planning": """
PM: Alright team, let's plan the next sprint. We have two weeks and about 40 story points of capacity.

Dev1: I can take the authentication refactor. That's estimated at 8 points and should take the full sprint.

Dev2: I'll pick up the payment integration. It's 13 points but I think we can get it done if we don't hit any API issues.

PM: Good. QA, when can you start testing the auth changes?

QA: I'll need at least 3 days of dev complete before I can start comprehensive testing. So ideally Dev1 finishes by day 7.

Dev1: That's tight but doable. I'll flag if I'm falling behind by midweek.

PM: Perfect. What about the bug backlog?

Dev2: We should allocate at least 5 points for critical bugs. There's that checkout issue that keeps coming up.

PM: Agreed. Dev1, can you squeeze that in?

Dev1: If it's just that one bug, yes. I'll fix it in the first few days before diving deep into auth.

PM: Great. So sprint goals: Auth refactor complete and tested, payment integration at least 80% done, and critical checkout bug fixed. QA starts testing auth by day 8. Everyone commit to this plan?

All: Committed.

PM: Excellent. Let's ship it!
"""
}


if __name__ == "__main__":
    # Test with sample transcript
    processor = MeetingProcessor()
    
    print("Processing sample transcript...")
    summary = processor.process_transcript(
        SAMPLE_TRANSCRIPTS["weekly_sync"],
        meeting_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    print(f"\n📋 {summary.title}")
    print(f"📅 {summary.date} | ⏱️ ~{summary.duration_minutes} min")
    print(f"👥 Attendees: {', '.join(summary.attendees)}")
    print(f"\n📝 Summary: {summary.summary}")
    
    print(f"\n✅ Action Items ({len(summary.action_items)}):")
    for action in summary.action_items:
        print(f"  [{action.priority.value.upper()}] {action.title}")
        print(f"      → {action.assignee} | Due: {action.due_date}")
