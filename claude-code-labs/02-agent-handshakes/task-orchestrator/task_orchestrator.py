"""
Task Decomposition Orchestrator - Project 3.4
Hierarchical pattern: Master agent delegates to specialized workers
"""

import json
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from anthropic import Anthropic

claude = Anthropic()


# ============== DATA STRUCTURES ==============

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkerType(str, Enum):
    RESEARCH = "research"
    CODE = "code"
    WRITE = "write"
    ANALYZE = "analyze"
    SUMMARIZE = "summarize"


@dataclass
class SubTask:
    """A subtask delegated to a worker"""
    id: str
    title: str
    description: str
    worker_type: WorkerType
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: str = ""
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['worker_type'] = self.worker_type.value
        d['status'] = self.status.value
        return d


@dataclass
class TaskPlan:
    """Orchestrator's plan for executing a complex task"""
    original_task: str
    goal: str
    subtasks: list[SubTask]
    execution_order: list[list[str]]
    
    def to_dict(self) -> dict:
        return {
            "original_task": self.original_task,
            "goal": self.goal,
            "subtasks": [st.to_dict() for st in self.subtasks],
            "execution_order": self.execution_order
        }


@dataclass
class TaskResult:
    """Final aggregated result"""
    task: str
    success: bool
    final_output: str
    subtask_results: dict
    execution_time_seconds: float
    total_tokens: int


# ============== ORCHESTRATOR AGENT ==============

ORCHESTRATOR_SYSTEM = """You are a Task Orchestrator Agent. Your job is to break down complex tasks into smaller, manageable subtasks and assign them to specialized workers.

Available worker types:
- "research": For gathering information, facts, data
- "code": For writing or analyzing code
- "write": For writing content, documentation, articles
- "analyze": For analyzing data, documents, situations
- "summarize": For condensing information

Guidelines:
1. Break the task into 2-6 subtasks (not too many, not too few)
2. Identify dependencies between subtasks
3. Group independent tasks for parallel execution
4. Each subtask should be focused and achievable
5. Consider what information each worker needs

OUTPUT FORMAT:
Respond with ONLY a JSON object:
{
    "goal": "The overall goal in one sentence",
    "subtasks": [
        {
            "id": "task_1",
            "title": "Short title",
            "description": "Detailed description of what this subtask should accomplish",
            "worker_type": "research|code|write|analyze|summarize",
            "dependencies": []
        },
        {
            "id": "task_2",
            "title": "Another task",
            "description": "Description...",
            "worker_type": "write",
            "dependencies": ["task_1"]
        }
    ],
    "execution_order": [
        ["task_1", "task_3"],
        ["task_2"]
    ]
}

execution_order groups tasks that can run in parallel. Tasks in later groups wait for earlier groups."""


def run_orchestrator_plan(task: str) -> tuple[TaskPlan, dict]:
    """Orchestrator creates a plan for the task."""
    
    prompt = f"""Break down this complex task into subtasks:

TASK: {task}

Create a plan with subtasks and their execution order."""

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=ORCHESTRATOR_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.content[0].text
    
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        
        subtasks = []
        for st in data.get("subtasks", []):
            subtasks.append(SubTask(
                id=st["id"],
                title=st["title"],
                description=st["description"],
                worker_type=WorkerType(st["worker_type"]),
                dependencies=st.get("dependencies", [])
            ))
        
        plan = TaskPlan(
            original_task=task,
            goal=data.get("goal", ""),
            subtasks=subtasks,
            execution_order=data.get("execution_order", [[st.id for st in subtasks]])
        )
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        plan = TaskPlan(
            original_task=task,
            goal=task,
            subtasks=[SubTask(
                id="task_1",
                title="Complete Task",
                description=task,
                worker_type=WorkerType.WRITE
            )],
            execution_order=[["task_1"]]
        )
    
    metadata = {
        "agent": "orchestrator",
        "action": "plan",
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    
    return plan, metadata


# ============== AGGREGATOR ==============

AGGREGATOR_SYSTEM = """You are a Task Aggregator. Your job is to combine results from multiple subtasks into a coherent final output.

Guidelines:
1. Synthesize all subtask results into a unified response
2. Maintain logical flow and coherence
3. Remove redundancy while keeping important details
4. Format appropriately for the original task
5. Ensure the final output fully addresses the original request

OUTPUT FORMAT:
Respond with the final, polished output that combines all subtask results.
Use appropriate formatting (markdown headers, lists, etc.) for readability."""


def run_orchestrator_aggregate(
    original_task: str,
    goal: str,
    subtask_results: dict[str, str]
) -> tuple[str, dict]:
    """Orchestrator aggregates subtask results into final output."""
    
    results_text = ""
    for task_id, result in subtask_results.items():
        results_text += f"\n## {task_id}\n{result}\n"
    
    prompt = f"""Combine these subtask results into a final output.

ORIGINAL TASK: {original_task}

GOAL: {goal}

SUBTASK RESULTS:
{results_text}

Create a coherent final output that addresses the original task."""

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        system=AGGREGATOR_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    
    metadata = {
        "agent": "orchestrator",
        "action": "aggregate",
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    
    return response.content[0].text, metadata


# ============== WORKER AGENTS ==============

WORKER_SYSTEMS = {
    WorkerType.RESEARCH: """You are a Research Worker. Your job is to gather information and facts.

Guidelines:
- Provide factual, well-organized information
- Include relevant details and examples
- Cite sources when possible
- Be thorough but concise

Respond with your research findings in a clear format.""",

    WorkerType.CODE: """You are a Code Worker. Your job is to write or analyze code.

Guidelines:
- Write clean, well-commented code
- Follow best practices for the language
- Include error handling where appropriate
- Explain your implementation decisions

Respond with code and explanations as needed.""",

    WorkerType.WRITE: """You are a Writing Worker. Your job is to write content.

Guidelines:
- Write clear, engaging content
- Match the appropriate tone and style
- Structure content logically
- Be concise but complete

Respond with the requested written content.""",

    WorkerType.ANALYZE: """You are an Analysis Worker. Your job is to analyze information.

Guidelines:
- Break down complex information
- Identify patterns and insights
- Provide clear conclusions
- Support findings with evidence

Respond with your analysis and conclusions.""",

    WorkerType.SUMMARIZE: """You are a Summary Worker. Your job is to condense information.

Guidelines:
- Capture key points accurately
- Maintain essential context
- Be concise without losing meaning
- Organize logically

Respond with a clear, concise summary."""
}


def run_worker(
    subtask: SubTask,
    context: str = "",
    dependency_results: dict[str, str] = None
) -> tuple[str, dict]:
    """Run a specialized worker agent."""
    
    system = WORKER_SYSTEMS.get(subtask.worker_type, WORKER_SYSTEMS[WorkerType.WRITE])
    
    prompt = f"""## Task: {subtask.title}

{subtask.description}"""

    if context:
        prompt += f"\n\n## Additional Context:\n{context}"
    
    if dependency_results:
        prompt += "\n\n## Results from Previous Tasks:"
        for task_id, result in dependency_results.items():
            prompt += f"\n\n### {task_id}:\n{result[:1000]}..."

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    
    metadata = {
        "agent": "worker",
        "worker_type": subtask.worker_type.value,
        "task_id": subtask.id,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    
    return response.content[0].text, metadata


# ============== MAIN ORCHESTRATION ==============

def execute_task(
    task: str,
    on_plan_complete: Callable = None,
    on_subtask_start: Callable = None,
    on_subtask_complete: Callable = None,
    on_aggregation_start: Callable = None,
    parallel: bool = True
) -> tuple[TaskResult, TaskPlan]:
    """
    Execute a complex task using the orchestrator pattern.
    
    Returns:
        (TaskResult, TaskPlan)
    """
    import time
    start_time = time.time()
    total_tokens = 0
    
    # Step 1: Plan
    plan, plan_meta = run_orchestrator_plan(task)
    total_tokens += plan_meta["input_tokens"] + plan_meta["output_tokens"]
    
    if on_plan_complete:
        on_plan_complete(plan)
    
    # Step 2: Execute subtasks
    results = {}
    
    for task_group in plan.execution_order:
        if parallel and len(task_group) > 1:
            with ThreadPoolExecutor(max_workers=len(task_group)) as executor:
                futures = {}
                
                for task_id in task_group:
                    subtask = next((st for st in plan.subtasks if st.id == task_id), None)
                    if not subtask:
                        continue
                    
                    if on_subtask_start:
                        on_subtask_start(subtask)
                    
                    subtask.status = TaskStatus.IN_PROGRESS
                    dep_results = {dep_id: results.get(dep_id, "") for dep_id in subtask.dependencies}
                    
                    future = executor.submit(run_worker, subtask, "", dep_results)
                    futures[future] = subtask
                
                for future in as_completed(futures):
                    subtask = futures[future]
                    try:
                        result, meta = future.result()
                        subtask.result = result
                        subtask.status = TaskStatus.COMPLETED
                        results[subtask.id] = result
                        total_tokens += meta["input_tokens"] + meta["output_tokens"]
                        
                        if on_subtask_complete:
                            on_subtask_complete(subtask, meta)
                    except Exception as e:
                        subtask.status = TaskStatus.FAILED
                        subtask.result = f"Error: {str(e)}"
        else:
            for task_id in task_group:
                subtask = next((st for st in plan.subtasks if st.id == task_id), None)
                if not subtask:
                    continue
                
                if on_subtask_start:
                    on_subtask_start(subtask)
                
                subtask.status = TaskStatus.IN_PROGRESS
                dep_results = {dep_id: results.get(dep_id, "") for dep_id in subtask.dependencies}
                
                try:
                    result, meta = run_worker(subtask, "", dep_results)
                    subtask.result = result
                    subtask.status = TaskStatus.COMPLETED
                    results[subtask.id] = result
                    total_tokens += meta["input_tokens"] + meta["output_tokens"]
                    
                    if on_subtask_complete:
                        on_subtask_complete(subtask, meta)
                except Exception as e:
                    subtask.status = TaskStatus.FAILED
                    subtask.result = f"Error: {str(e)}"
    
    # Step 3: Aggregate
    if on_aggregation_start:
        on_aggregation_start()
    
    final_output, agg_meta = run_orchestrator_aggregate(task, plan.goal, results)
    total_tokens += agg_meta["input_tokens"] + agg_meta["output_tokens"]
    
    execution_time = time.time() - start_time
    
    task_result = TaskResult(
        task=task,
        success=all(st.status == TaskStatus.COMPLETED for st in plan.subtasks),
        final_output=final_output,
        subtask_results=results,
        execution_time_seconds=round(execution_time, 2),
        total_tokens=total_tokens
    )
    
    return task_result, plan


# ============== SAMPLE TASKS ==============

SAMPLE_TASKS = [
    "Create a technical blog post about microservices architecture, including code examples in Python and a comparison table",
    "Research the top 5 JavaScript frameworks in 2026, analyze their pros/cons, and write a recommendation guide",
    "Build a REST API design document with endpoint specifications, data models, and implementation notes",
    "Create a project proposal for a mobile app including market research, features, and technical requirements",
    "Write a comprehensive guide to Docker containerization with practical examples and best practices",
]


if __name__ == "__main__":
    task = SAMPLE_TASKS[0]
    
    print(f"Task: {task}\n")
    print("=" * 60)
    
    def on_plan(plan):
        print(f"\n📋 Plan: {len(plan.subtasks)} subtasks")
        for st in plan.subtasks:
            print(f"  - [{st.worker_type.value}] {st.title}")
    
    def on_start(subtask):
        print(f"\n⏳ Starting: {subtask.title}")
    
    def on_complete(subtask, meta):
        print(f"✅ Completed: {subtask.title}")
    
    def on_agg():
        print("\n🔄 Aggregating...")
    
    result, plan = execute_task(
        task,
        on_plan_complete=on_plan,
        on_subtask_start=on_start,
        on_subtask_complete=on_complete,
        on_aggregation_start=on_agg
    )
    
    print("\n" + "=" * 60)
    print(result.final_output[:2000])
    print(f"\n⏱️ Time: {result.execution_time_seconds}s | 🎟️ Tokens: {result.total_tokens}")
