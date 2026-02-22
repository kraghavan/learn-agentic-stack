"""
Multi-Agent Orchestrator - Project 3.1
Coordinates Researcher and Writer agents with structured handoffs.
"""

import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

from anthropic import Anthropic

claude = Anthropic()


# ============== HANDOFF SCHEMA ==============

@dataclass
class ResearchNotes:
    """Structured output from Researcher → Writer"""
    topic: str
    summary: str
    key_facts: list[str]
    sources: list[dict]  # {"title": str, "url": str, "snippet": str}
    suggested_sections: list[str]
    target_audience: str
    tone: str
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "ResearchNotes":
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class ArticleDraft:
    """Structured output from Writer"""
    title: str
    outline: list[str]
    draft: str
    word_count: int
    revision_notes: str
    final_article: str


# ============== RESEARCHER AGENT ==============

RESEARCHER_SYSTEM = """You are a Research Agent specialized in gathering and organizing information.

Your job is to:
1. Understand the user's topic/query
2. Gather relevant information and facts
3. Identify key points and themes
4. Suggest a structure for an article
5. Note potential sources

OUTPUT FORMAT:
You MUST respond with ONLY a JSON object (no markdown, no explanation):
{
    "topic": "The main topic",
    "summary": "A 2-3 sentence summary of the topic",
    "key_facts": ["fact 1", "fact 2", "fact 3", ...],
    "sources": [
        {"title": "Source name", "url": "https://...", "snippet": "Key quote or info"}
    ],
    "suggested_sections": ["Introduction", "Section 1", "Section 2", "Conclusion"],
    "target_audience": "Who this is for",
    "tone": "professional/casual/technical/etc"
}

Be thorough but concise. Focus on factual, useful information."""


def run_researcher(query: str, context: str = "") -> tuple[ResearchNotes, dict]:
    """
    Run the Researcher Agent.
    
    Returns:
        (ResearchNotes, metadata)
    """
    messages = [{"role": "user", "content": f"Research this topic for an article:\n\n{query}"}]
    
    if context:
        messages[0]["content"] += f"\n\nAdditional context: {context}"
    
    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=RESEARCHER_SYSTEM,
        messages=messages
    )
    
    content = response.content[0].text
    
    # Parse JSON response
    try:
        # Clean up response if needed
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        notes = ResearchNotes(**data)
    except (json.JSONDecodeError, TypeError) as e:
        # Fallback if parsing fails
        notes = ResearchNotes(
            topic=query,
            summary=content[:500],
            key_facts=["Research parsing failed - using raw content"],
            sources=[],
            suggested_sections=["Introduction", "Main Content", "Conclusion"],
            target_audience="General",
            tone="professional"
        )
    
    metadata = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "model": "claude-sonnet-4-20250514",
    }
    
    return notes, metadata


# ============== WRITER AGENT ==============

WRITER_SYSTEM = """You are a Writer Agent specialized in creating polished articles.

You will receive research notes from a Research Agent. Your job is to:
1. Create a clear outline based on the research
2. Write a compelling first draft
3. Polish and refine into a final article

OUTPUT FORMAT:
You MUST respond with ONLY a JSON object (no markdown, no explanation):
{
    "title": "Article Title",
    "outline": ["I. Introduction", "II. Section 1", "III. Section 2", "IV. Conclusion"],
    "draft": "The first draft of the article...",
    "word_count": 500,
    "revision_notes": "Notes on what was improved",
    "final_article": "The polished final article with proper formatting..."
}

Guidelines:
- Match the tone specified in the research notes
- Include all key facts naturally
- Use clear structure with headings (## Heading)
- Write for the target audience
- Aim for 400-800 words unless specified otherwise
- Make it engaging and informative"""


def run_writer(research_notes: ResearchNotes) -> tuple[ArticleDraft, dict]:
    """
    Run the Writer Agent.
    
    Args:
        research_notes: Output from Researcher Agent
    
    Returns:
        (ArticleDraft, metadata)
    """
    handoff_content = f"""## Research Notes from Researcher Agent

**Topic:** {research_notes.topic}

**Summary:** {research_notes.summary}

**Key Facts:**
{chr(10).join(f"- {fact}" for fact in research_notes.key_facts)}

**Suggested Sections:**
{chr(10).join(f"- {section}" for section in research_notes.suggested_sections)}

**Target Audience:** {research_notes.target_audience}

**Tone:** {research_notes.tone}

**Sources:**
{chr(10).join(f"- {s.get('title', 'Unknown')}: {s.get('snippet', '')}" for s in research_notes.sources)}

---

Please write the article based on these research notes."""

    messages = [{"role": "user", "content": handoff_content}]
    
    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        system=WRITER_SYSTEM,
        messages=messages
    )
    
    content = response.content[0].text
    
    # Parse JSON response
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        article = ArticleDraft(**data)
    except (json.JSONDecodeError, TypeError) as e:
        # Fallback
        article = ArticleDraft(
            title=f"Article: {research_notes.topic}",
            outline=research_notes.suggested_sections,
            draft=content,
            word_count=len(content.split()),
            revision_notes="Parsing failed - showing raw output",
            final_article=content
        )
    
    metadata = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "model": "claude-sonnet-4-20250514",
    }
    
    return article, metadata


# ============== ORCHESTRATOR ==============

def run_pipeline(
    query: str,
    context: str = "",
    on_research_complete: callable = None,
    on_writing_complete: callable = None
) -> dict:
    """
    Run the full Researcher → Writer pipeline.
    
    Args:
        query: User's topic/request
        context: Additional context
        on_research_complete: Callback after research (optional)
        on_writing_complete: Callback after writing (optional)
    
    Returns:
        {
            "research_notes": ResearchNotes,
            "article": ArticleDraft,
            "metadata": {...}
        }
    """
    result = {
        "query": query,
        "stages": [],
        "metadata": {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
        }
    }
    
    # Stage 1: Research
    research_notes, research_meta = run_researcher(query, context)
    result["research_notes"] = research_notes
    result["stages"].append({
        "agent": "researcher",
        "status": "complete",
        "metadata": research_meta
    })
    result["metadata"]["total_input_tokens"] += research_meta["input_tokens"]
    result["metadata"]["total_output_tokens"] += research_meta["output_tokens"]
    
    if on_research_complete:
        on_research_complete(research_notes)
    
    # Stage 2: Writing
    article, writer_meta = run_writer(research_notes)
    result["article"] = article
    result["stages"].append({
        "agent": "writer",
        "status": "complete", 
        "metadata": writer_meta
    })
    result["metadata"]["total_input_tokens"] += writer_meta["input_tokens"]
    result["metadata"]["total_output_tokens"] += writer_meta["output_tokens"]
    
    if on_writing_complete:
        on_writing_complete(article)
    
    return result


if __name__ == "__main__":
    # Test
    result = run_pipeline("The future of renewable energy in 2030")
    
    print("=== RESEARCH NOTES ===")
    print(result["research_notes"].to_json())
    
    print("\n=== FINAL ARTICLE ===")
    print(result["article"].final_article)
    
    print("\n=== METADATA ===")
    print(f"Total tokens: {result['metadata']}")
