# 📋 Meeting Pipeline - Architecture Diagrams

## System Overview

```mermaid
flowchart TB
    subgraph UI["🖥️ Streamlit UI"]
        Input["📥 Input Stage"]
        Transcript["📝 Transcript Stage"]
        Analysis["📊 Analysis Stage"]
        Actions["🎯 Actions Stage"]
        Complete["✅ Complete Stage"]
    end

    subgraph Processing["⚙️ Meeting Processor"]
        Transcriber["🎙️ Transcriber"]
        Analyzer["🧠 Analyzer"]
    end

    subgraph Integrations["🔗 Integration Hub"]
        Jira["🎫 Mock Jira"]
        Email["📧 Email Drafter"]
        Calendar["📅 Mock Calendar"]
    end

    subgraph External["☁️ External APIs"]
        Whisper["OpenAI Whisper"]
        Claude["Claude API"]
    end

    Input --> Transcriber
    Transcriber --> Whisper
    Transcriber --> Transcript
    Transcript --> Analyzer
    Analyzer --> Claude
    Analyzer --> Analysis
    Analysis --> Actions
    Actions --> Integrations
    Integrations --> Complete

    Jira --> Claude
    Email --> Claude
```

## End-to-End Pipeline

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit
    participant Proc as MeetingProcessor
    participant Whisper as OpenAI Whisper
    participant Claude as Claude API
    participant Hub as IntegrationHub

    User->>UI: Upload audio/paste transcript
    
    alt Audio Input
        UI->>Proc: process_audio()
        Proc->>Whisper: transcribe()
        Whisper-->>Proc: transcript text
    else Text Input
        UI->>Proc: process_transcript()
    end
    
    Proc->>Claude: analyze(transcript)
    Claude-->>Proc: MeetingSummary + ActionItems
    Proc-->>UI: Display summary
    
    User->>UI: Generate outputs
    UI->>Hub: process_meeting_actions()
    
    par Create Tickets
        Hub->>Hub: jira.create_tickets()
    and Draft Email
        Hub->>Claude: draft_followup()
        Claude-->>Hub: email content
    and Create Events
        Hub->>Hub: calendar.create_events()
    end
    
    Hub-->>UI: All outputs
    UI-->>User: Display & download
```

## Data Flow

```mermaid
flowchart LR
    subgraph Input["📥 Input"]
        Audio["🎤 Audio\n(.mp3, .wav)"]
        Text["📝 Text\n(paste/type)"]
        Sample["📄 Sample\n(built-in)"]
    end

    subgraph Process["⚙️ Process"]
        Transcribe["Whisper\nTranscription"]
        Extract["Claude\nExtraction"]
    end

    subgraph Data["📊 Extracted"]
        Summary["📋 Summary"]
        Points["💡 Key Points"]
        Decisions["✅ Decisions"]
        Actions["🎯 Actions"]
    end

    subgraph Output["📤 Outputs"]
        Tickets["🎫 Jira\nTickets"]
        Email["📧 Follow-up\nEmail"]
        Events["📅 Calendar\nEvents"]
        Export["📥 JSON\nExport"]
    end

    Audio --> Transcribe
    Text --> Extract
    Sample --> Extract
    Transcribe --> Extract
    
    Extract --> Summary
    Extract --> Points
    Extract --> Decisions
    Extract --> Actions
    
    Actions --> Tickets
    Summary --> Email
    Actions --> Email
    Actions --> Events
    
    Summary --> Export
    Actions --> Export
    Tickets --> Export
```

## Action Item Extraction

```mermaid
flowchart TD
    Transcript["📝 Meeting Transcript"]
    
    Transcript --> Claude["🧠 Claude Analysis"]
    
    Claude --> Parse["Parse JSON Response"]
    
    Parse --> Actions["🎯 Action Items"]
    
    Actions --> A1["Action 1"]
    Actions --> A2["Action 2"]
    Actions --> A3["Action N"]
    
    subgraph ActionFields["Action Item Fields"]
        Title["📌 Title"]
        Desc["📝 Description"]
        Assignee["👤 Assignee"]
        Due["📅 Due Date"]
        Priority["🔴🟡🟢 Priority"]
        Type["📋 Type"]
        Context["💬 Context Quote"]
    end
    
    A1 --> ActionFields
```

## Integration Hub

```mermaid
flowchart TB
    subgraph Hub["🔗 IntegrationHub"]
        direction TB
        Process["process_meeting_actions()"]
    end

    subgraph Jira["🎫 MockJiraClient"]
        CreateTicket["create_ticket()"]
        ListTickets["list_tickets()"]
        Tickets[("Tickets Store")]
    end

    subgraph Email["📧 EmailDrafter"]
        DraftFollowup["draft_followup()"]
        DraftReminder["draft_reminder()"]
        Drafts[("Drafts Store")]
    end

    subgraph Calendar["📅 MockCalendarClient"]
        CreateMeeting["create_followup_meeting()"]
        CreateReminder["create_deadline_reminder()"]
        Events[("Events Store")]
    end

    Process --> CreateTicket
    Process --> DraftFollowup
    Process --> CreateMeeting

    CreateTicket --> Tickets
    DraftFollowup --> Drafts
    CreateMeeting --> Events
```

## UI State Machine

```mermaid
stateDiagram-v2
    [*] --> Input
    
    Input --> Transcript: Upload/Paste
    Transcript --> Analysis: Analyze
    Analysis --> Actions: View Actions
    Actions --> Complete: Generate
    
    Complete --> Input: Start Over
    
    Transcript --> Input: Back
    Analysis --> Transcript: Back
    Actions --> Analysis: Back

    state Input {
        [*] --> SelectSource
        SelectSource --> PasteText: Tab 1
        SelectSource --> UploadAudio: Tab 2
        SelectSource --> UseSample: Tab 3
    }

    state Analysis {
        [*] --> ShowSummary
        ShowSummary --> ShowKeyPoints
        ShowKeyPoints --> ShowDecisions
    }

    state Actions {
        [*] --> ListActions
        ListActions --> SelectOutputs
        SelectOutputs --> Generate
    }
```

## Data Models

```mermaid
classDiagram
    class MeetingSummary {
        +str title
        +str date
        +int duration_minutes
        +list~str~ attendees
        +str summary
        +list~str~ key_points
        +list~str~ decisions
        +list~ActionItem~ action_items
        +str next_steps
        +to_dict() dict
    }

    class ActionItem {
        +str id
        +str title
        +str description
        +str assignee
        +str due_date
        +Priority priority
        +ActionType action_type
        +str context
        +to_dict() dict
    }

    class JiraTicket {
        +str key
        +str project
        +str summary
        +str description
        +str assignee
        +str priority
        +str due_date
        +str status
        +list~str~ labels
        +to_jira_format() str
    }

    class Email {
        +list~str~ to
        +list~str~ cc
        +str subject
        +str body
        +to_email_format() str
    }

    class CalendarEvent {
        +str id
        +str title
        +str start
        +str end
        +list~str~ attendees
        +str description
        +to_calendar_format() str
    }

    MeetingSummary "1" --> "*" ActionItem
    ActionItem --> JiraTicket : creates
    MeetingSummary --> Email : creates
    ActionItem --> CalendarEvent : creates
```

## Token Flow

```mermaid
flowchart LR
    subgraph Analysis["📊 Meeting Analysis ~$0.04"]
        A1["Transcript\n~1500 tokens"]
        A2["System Prompt\n~500 tokens"]
        A3["JSON Output\n~500 tokens"]
    end

    subgraph Email["📧 Email Draft ~$0.02"]
        E1["Summary Input\n~400 tokens"]
        E2["Email Output\n~600 tokens"]
    end

    subgraph Total["💰 Total per Meeting"]
        T1["~3,500 tokens"]
        T2["~$0.06"]
    end

    A1 --> A2 --> A3
    E1 --> E2
    A3 --> Total
    E2 --> Total
```

## Deployment Architecture

```mermaid
flowchart TB
    subgraph Docker["🐳 Docker Container"]
        Streamlit["Streamlit\n:8501"]
        Python["Python 3.11"]
        FFmpeg["FFmpeg\n(audio)"]
    end

    subgraph Volumes["📁 Volumes"]
        Uploads["./uploads"]
    end

    subgraph Env["🔐 Environment"]
        Anthropic["ANTHROPIC_API_KEY"]
        OpenAI["OPENAI_API_KEY\n(optional)"]
    end

    subgraph External["☁️ External"]
        ClaudeAPI["Claude API"]
        WhisperAPI["Whisper API"]
    end

    User["👤 User\n:8501"] --> Streamlit
    Volumes --> Docker
    Env --> Docker
    Docker --> ClaudeAPI
    Docker --> WhisperAPI
```

---

## Quick Reference

| Component | File | Purpose |
|-----------|------|---------|
| 🎙️ Transcriber | `meeting_processor.py` | Whisper integration |
| 🧠 Analyzer | `meeting_processor.py` | Claude extraction |
| 🎫 Jira | `meeting_integrations.py` | Mock ticket creation |
| 📧 Email | `meeting_integrations.py` | AI email drafting |
| 📅 Calendar | `meeting_integrations.py` | Event creation |
| 🖥️ UI | `meeting_app.py` | Streamlit interface |

---

*Part of [learn-agentic-stack](https://github.com/kraghavan/learn-agentic-stack) - Project 4.3*