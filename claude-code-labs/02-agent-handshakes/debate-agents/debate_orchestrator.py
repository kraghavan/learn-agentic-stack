"""
Debate Agents - Project 3.3
Adversarial pattern: Pro vs Con with Synthesizer
"""

import json
from datetime import datetime
from typing import Generator
from dataclasses import dataclass, asdict, field

from anthropic import Anthropic

claude = Anthropic()


# ============== DATA STRUCTURES ==============

@dataclass
class Argument:
    """A single argument in the debate"""
    side: str  # "pro" or "con"
    round: int
    main_point: str
    supporting_points: list[str]
    evidence: list[str]
    rebuttal_to: str = ""  # Response to opponent's previous argument
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DebateRound:
    """One round of debate (pro + con)"""
    round_number: int
    pro_argument: Argument
    con_argument: Argument


@dataclass
class Synthesis:
    """Final synthesis from the Synthesizer agent"""
    topic: str
    summary: str
    pro_strengths: list[str]
    con_strengths: list[str]
    areas_of_agreement: list[str]
    key_tensions: list[str]
    nuanced_conclusion: str
    recommendation: str  # What a reasonable person might conclude
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Debate:
    """Complete debate record"""
    topic: str
    rounds: list[DebateRound] = field(default_factory=list)
    synthesis: Synthesis = None
    metadata: dict = field(default_factory=dict)


# ============== AGENT: PRO ==============

PRO_SYSTEM = """You are a Pro Debater Agent. Your job is to argue IN FAVOR of the given topic.

Guidelines:
1. Make strong, logical arguments supporting the position
2. Use evidence and examples where possible
3. Address counterarguments when responding to the Con side
4. Be persuasive but intellectually honest
5. Don't strawman - engage with the strongest opposing arguments

OUTPUT FORMAT:
Respond with ONLY a JSON object:
{
    "main_point": "Your central argument this round",
    "supporting_points": ["Supporting point 1", "Supporting point 2"],
    "evidence": ["Evidence or example 1", "Evidence or example 2"],
    "rebuttal_to": "If responding to Con, address their argument here (empty string if first round)"
}

Be concise but compelling. Each round should build on previous arguments."""


def run_pro_agent(
    topic: str,
    round_num: int,
    debate_history: list[Argument] = None
) -> tuple[Argument, dict]:
    """Run the Pro agent for one round."""
    
    # Build context from debate history
    history_text = ""
    if debate_history:
        history_text = "\n\n## Previous Arguments:\n"
        for arg in debate_history:
            side = "PRO" if arg.side == "pro" else "CON"
            history_text += f"\n**{side} (Round {arg.round}):** {arg.main_point}\n"
            for point in arg.supporting_points:
                history_text += f"  - {point}\n"
    
    prompt = f"""## Debate Topic: {topic}

## Your Position: ARGUE IN FAVOR (Pro)

## Round: {round_num}
{history_text}

{"Make your opening argument for this position." if round_num == 1 else "Continue the debate. Address the Con arguments and strengthen your position."}"""

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=PRO_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.content[0].text
    
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        argument = Argument(
            side="pro",
            round=round_num,
            main_point=data.get("main_point", ""),
            supporting_points=data.get("supporting_points", []),
            evidence=data.get("evidence", []),
            rebuttal_to=data.get("rebuttal_to", "")
        )
    except (json.JSONDecodeError, TypeError):
        argument = Argument(
            side="pro",
            round=round_num,
            main_point=content[:500],
            supporting_points=[],
            evidence=[],
            rebuttal_to=""
        )
    
    metadata = {
        "agent": "pro",
        "round": round_num,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    
    return argument, metadata


# ============== AGENT: CON ==============

CON_SYSTEM = """You are a Con Debater Agent. Your job is to argue AGAINST the given topic.

Guidelines:
1. Make strong, logical arguments opposing the position
2. Use evidence and examples where possible
3. Directly rebut the Pro side's arguments
4. Be persuasive but intellectually honest
5. Engage with the strongest pro arguments, not strawmen

OUTPUT FORMAT:
Respond with ONLY a JSON object:
{
    "main_point": "Your central argument this round",
    "supporting_points": ["Supporting point 1", "Supporting point 2"],
    "evidence": ["Evidence or example 1", "Evidence or example 2"],
    "rebuttal_to": "Directly address Pro's argument here"
}

Be concise but compelling. Focus on finding weaknesses in Pro's position."""


def run_con_agent(
    topic: str,
    round_num: int,
    debate_history: list[Argument] = None
) -> tuple[Argument, dict]:
    """Run the Con agent for one round."""
    
    history_text = ""
    if debate_history:
        history_text = "\n\n## Previous Arguments:\n"
        for arg in debate_history:
            side = "PRO" if arg.side == "pro" else "CON"
            history_text += f"\n**{side} (Round {arg.round}):** {arg.main_point}\n"
            for point in arg.supporting_points:
                history_text += f"  - {point}\n"
    
    prompt = f"""## Debate Topic: {topic}

## Your Position: ARGUE AGAINST (Con)

## Round: {round_num}
{history_text}

Respond to Pro's arguments and present your counter-arguments."""

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=CON_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.content[0].text
    
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        argument = Argument(
            side="con",
            round=round_num,
            main_point=data.get("main_point", ""),
            supporting_points=data.get("supporting_points", []),
            evidence=data.get("evidence", []),
            rebuttal_to=data.get("rebuttal_to", "")
        )
    except (json.JSONDecodeError, TypeError):
        argument = Argument(
            side="con",
            round=round_num,
            main_point=content[:500],
            supporting_points=[],
            evidence=[],
            rebuttal_to=""
        )
    
    metadata = {
        "agent": "con",
        "round": round_num,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    
    return argument, metadata


# ============== AGENT: SYNTHESIZER ==============

SYNTHESIZER_SYSTEM = """You are a Synthesis Agent. Your job is to provide a balanced, nuanced analysis of a debate.

Guidelines:
1. Fairly represent both sides' strongest arguments
2. Identify areas of genuine agreement
3. Highlight key tensions that remain unresolved
4. Provide a nuanced conclusion that acknowledges complexity
5. Avoid false balance - if one side has stronger arguments, note it
6. Be helpful to someone trying to form their own opinion

OUTPUT FORMAT:
Respond with ONLY a JSON object:
{
    "summary": "Brief 2-3 sentence summary of the debate",
    "pro_strengths": ["Strongest pro argument 1", "Strongest pro argument 2"],
    "con_strengths": ["Strongest con argument 1", "Strongest con argument 2"],
    "areas_of_agreement": ["Point both sides might agree on"],
    "key_tensions": ["Unresolved tension 1", "Fundamental disagreement"],
    "nuanced_conclusion": "A thoughtful paragraph synthesizing the debate",
    "recommendation": "What a reasonable person might conclude"
}

Be intellectually honest and help the reader think through the issue."""


def run_synthesizer(
    topic: str,
    all_arguments: list[Argument]
) -> tuple[Synthesis, dict]:
    """Run the Synthesizer agent."""
    
    # Format debate history
    debate_text = ""
    for arg in all_arguments:
        side = "PRO" if arg.side == "pro" else "CON"
        debate_text += f"\n### {side} (Round {arg.round})\n"
        debate_text += f"**Main Point:** {arg.main_point}\n"
        if arg.supporting_points:
            debate_text += "**Supporting Points:**\n"
            for point in arg.supporting_points:
                debate_text += f"  - {point}\n"
        if arg.rebuttal_to:
            debate_text += f"**Rebuttal:** {arg.rebuttal_to}\n"
    
    prompt = f"""## Debate Topic: {topic}

## Full Debate Transcript:
{debate_text}

Please synthesize this debate into a balanced analysis."""

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYNTHESIZER_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.content[0].text
    
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        synthesis = Synthesis(
            topic=topic,
            summary=data.get("summary", ""),
            pro_strengths=data.get("pro_strengths", []),
            con_strengths=data.get("con_strengths", []),
            areas_of_agreement=data.get("areas_of_agreement", []),
            key_tensions=data.get("key_tensions", []),
            nuanced_conclusion=data.get("nuanced_conclusion", ""),
            recommendation=data.get("recommendation", "")
        )
    except (json.JSONDecodeError, TypeError):
        synthesis = Synthesis(
            topic=topic,
            summary="Synthesis parsing failed",
            pro_strengths=[],
            con_strengths=[],
            areas_of_agreement=[],
            key_tensions=[],
            nuanced_conclusion=content,
            recommendation=""
        )
    
    metadata = {
        "agent": "synthesizer",
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    
    return synthesis, metadata


# ============== ORCHESTRATOR ==============

def run_debate(
    topic: str,
    num_rounds: int = 3,
    on_argument: callable = None
) -> Debate:
    """
    Run a full debate.
    
    Args:
        topic: The debate topic
        num_rounds: Number of rounds (default 3)
        on_argument: Callback after each argument (for live updates)
    
    Returns:
        Complete Debate object
    """
    debate = Debate(
        topic=topic,
        metadata={
            "num_rounds": num_rounds,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
        }
    )
    
    all_arguments = []
    
    # Run debate rounds
    for round_num in range(1, num_rounds + 1):
        # Pro argues first
        pro_arg, pro_meta = run_pro_agent(topic, round_num, all_arguments)
        all_arguments.append(pro_arg)
        debate.metadata["total_input_tokens"] += pro_meta["input_tokens"]
        debate.metadata["total_output_tokens"] += pro_meta["output_tokens"]
        
        if on_argument:
            on_argument(pro_arg, pro_meta)
        
        # Con responds
        con_arg, con_meta = run_con_agent(topic, round_num, all_arguments)
        all_arguments.append(con_arg)
        debate.metadata["total_input_tokens"] += con_meta["input_tokens"]
        debate.metadata["total_output_tokens"] += con_meta["output_tokens"]
        
        if on_argument:
            on_argument(con_arg, con_meta)
        
        # Record round
        debate.rounds.append(DebateRound(
            round_number=round_num,
            pro_argument=pro_arg,
            con_argument=con_arg
        ))
    
    # Synthesize
    synthesis, synth_meta = run_synthesizer(topic, all_arguments)
    debate.synthesis = synthesis
    debate.metadata["total_input_tokens"] += synth_meta["input_tokens"]
    debate.metadata["total_output_tokens"] += synth_meta["output_tokens"]
    
    return debate


def run_debate_streaming(
    topic: str,
    num_rounds: int = 3
) -> Generator:
    """
    Run debate with streaming updates.
    Yields each argument as it's generated.
    """
    all_arguments = []
    
    for round_num in range(1, num_rounds + 1):
        # Pro
        pro_arg, pro_meta = run_pro_agent(topic, round_num, all_arguments)
        all_arguments.append(pro_arg)
        yield {"type": "argument", "data": pro_arg, "meta": pro_meta}
        
        # Con
        con_arg, con_meta = run_con_agent(topic, round_num, all_arguments)
        all_arguments.append(con_arg)
        yield {"type": "argument", "data": con_arg, "meta": con_meta}
    
    # Synthesis
    synthesis, synth_meta = run_synthesizer(topic, all_arguments)
    yield {"type": "synthesis", "data": synthesis, "meta": synth_meta}


# ============== SAMPLE TOPICS ==============

SAMPLE_TOPICS = [
    "Remote work should be the default for knowledge workers",
    "Social media has done more harm than good for society",
    "AI will create more jobs than it eliminates",
    "College degrees are overvalued in today's job market",
    "Electric vehicles should replace all gas-powered cars by 2035",
    "Universal Basic Income is a viable solution to automation",
    "Space exploration funding should be increased significantly",
    "Cryptocurrencies will eventually replace traditional currencies",
]


if __name__ == "__main__":
    # Test
    topic = "Remote work should be the default for knowledge workers"
    
    print(f"Debating: {topic}\n")
    print("=" * 60)
    
    def print_argument(arg, meta):
        side = "🟢 PRO" if arg.side == "pro" else "🔴 CON"
        print(f"\n{side} (Round {arg.round})")
        print(f"Main Point: {arg.main_point}")
        print("-" * 40)
    
    debate = run_debate(topic, num_rounds=2, on_argument=print_argument)
    
    print("\n" + "=" * 60)
    print("SYNTHESIS")
    print("=" * 60)
    print(f"\n{debate.synthesis.nuanced_conclusion}")
    print(f"\nRecommendation: {debate.synthesis.recommendation}")
