"""Top-level routing between the structured-data path and the semantic path.

A LlamaIndex RouterQueryEngine (with a PydanticSingleSelector) reads each query
and picks one of two tools:

- structured_data: count / filter / list over the extracted decisions, issues,
  and work-log. Answered directly from store.py — exact and reproducible, no LLM
  synthesis. The selector only chooses the tool; it does not extract arguments,
  so this engine runs a small QueryIntent classification to pick the exact store
  query + args (e.g. status="open").
- semantic_search: open-ended / explanatory questions, answered by the existing
  RAGWorkflow (retrieve -> rerank -> confidence/retry -> synthesize).

build_router_engine(workflow) wires it together; main.py owns the workflow and
passes it in (keeps this module free of a circular import).
"""

import asyncio
from typing import Literal

from pydantic import BaseModel, Field
from llama_index.core import PromptTemplate
from llama_index.core.query_engine import CustomQueryEngine, RouterQueryEngine
from llama_index.core.selectors import PydanticSingleSelector
from llama_index.core.tools import QueryEngineTool
from llama_index.core.base.response.schema import Response
from llama_index.llms.openai import OpenAI

from config import OPENAI_API_KEY, LLM_MODEL
import store

# temperature 0 — routing and intent should be stable for the same question
router_llm = OpenAI(api_key=OPENAI_API_KEY, model=LLM_MODEL, temperature=0)


# ---------- intent: which structured query + args ----------

class QueryIntent(BaseModel):
    """The exact store query (and args) to answer a structured question."""

    tool: Literal[
        "count_issues_by_type",
        "issues_by_status",
        "issues_by_type",
        "decisions_sorted",
        "work_log_sorted",
        "behavior_changes",
    ] = Field(description="Which store query answers the question.")
    status: Literal["open", "resolved", "accepted"] | None = Field(
        default=None, description="Required only for tool='issues_by_status'."
    )
    type: Literal["bug", "limitation", "risk", "edge_case", "future_concern"] | None = Field(
        default=None, description="Required only for tool='issues_by_type'."
    )


INTENT_PROMPT = PromptTemplate(
    "The question below is about a software project's recorded decisions, issues, "
    "and work-log, and is known to be a count/filter/list request. Pick the store "
    "query that answers it:\n"
    "- count_issues_by_type: how many issues / breakdown by type.\n"
    "- issues_by_status: issues filtered by status; set status to open/resolved/accepted.\n"
    "- issues_by_type: issues of one type; set type to bug/limitation/risk/edge_case/future_concern.\n"
    "- decisions_sorted: list the decisions.\n"
    "- work_log_sorted: list the work-log sessions.\n"
    "- behavior_changes: work-log sessions that changed app behavior.\n\n"
    "Set 'status' only for issues_by_status and 'type' only for issues_by_type.\n\n"
    "Question: {query}"
)


def classify(query: str) -> QueryIntent:
    """Map a structured question to its exact store query + args."""
    structured = router_llm.as_structured_llm(QueryIntent)
    return structured.complete(INTENT_PROMPT.format(query=query)).raw


# ---------- formatting: data -> markdown ----------

def _fmt_issues(header: str, issues) -> str:
    if not issues:
        return f"**{header}**\n\n_None found._"
    lines = [f"**{header}** ({len(issues)})\n"]
    for i in issues:
        srcs = ", ".join(i.source_files)
        lines.append(f"- **{i.title}** — `{i.type}`/`{i.status}`  \n  {i.description}  \n  _sources: {srcs}_")
    return "\n".join(lines)


def run_structured(intent: QueryIntent) -> str:
    """Dispatch a structured intent to store.py and return a markdown answer."""
    t = intent.tool

    if t == "count_issues_by_type":
        counts = store.count_issues_by_type()
        total = sum(counts.values())
        rows = "\n".join(f"- `{k}`: {v}" for k, v in sorted(counts.items()))
        return f"**Issues by type** (total {total})\n\n{rows}"

    if t == "issues_by_status":
        if not intent.status:
            return "Which status — open, resolved, or accepted?"
        return _fmt_issues(f"Issues with status '{intent.status}'", store.issues_by_status(intent.status))

    if t == "issues_by_type":
        if not intent.type:
            return "Which type — bug, limitation, risk, edge_case, or future_concern?"
        return _fmt_issues(f"Issues of type '{intent.type}'", store.issues_by_type(intent.type))

    if t == "decisions_sorted":
        decisions = store.decisions_sorted()
        if not decisions:
            return "_No decisions found._"
        rows = "\n".join(f"- **{d.id or '—'}** {d.title} ({d.date or 'no date'})  \n  {d.decision}" for d in decisions)
        return f"**Decisions** ({len(decisions)}, newest first)\n\n{rows}"

    if t == "work_log_sorted":
        entries = store.work_log_sorted()
        if not entries:
            return "_No work-log entries found._"
        rows = "\n".join(f"- **{w.date}** — {w.title}  \n  {w.summary}" for w in entries)
        return f"**Work log** ({len(entries)}, newest first)\n\n{rows}"

    if t == "behavior_changes":
        entries = store.behavior_changes()
        if not entries:
            return "_No work-log sessions changed app behavior._"
        rows = "\n".join(f"- **{w.date}** — {w.title}" for w in entries)
        return f"**Sessions that changed behavior** ({len(entries)})\n\n{rows}"

    return "_Could not map this question to a structured query._"


# ---------- query engines (the two router tools) ----------

_workflow = None   # the semantic RAGWorkflow instance, injected by build_router_engine


class StructuredQueryEngine(CustomQueryEngine):
    """Answers count/filter/list questions directly from the structured store."""

    def custom_query(self, query_str: str) -> Response:
        answer = run_structured(classify(query_str))
        return Response(response=answer, source_nodes=[])


class SemanticQueryEngine(CustomQueryEngine):
    """Answers open-ended questions via the existing semantic RAGWorkflow."""

    async def acustom_query(self, query_str: str) -> Response:
        result = await _workflow.run(user_query=query_str)
        return Response(response=result["answer"], source_nodes=result["nodes"])

    def custom_query(self, query_str: str) -> Response:   # sync fallback; aquery uses acustom_query
        return asyncio.run(self.acustom_query(query_str))


def build_router_engine(workflow) -> RouterQueryEngine:
    """Wire the RouterQueryEngine over the structured and semantic tools."""
    global _workflow
    _workflow = workflow

    structured_tool = QueryEngineTool.from_defaults(
        query_engine=StructuredQueryEngine(),
        name="structured_data",
        description=(
            "Count, filter, or list the project's recorded decisions, issues "
            "(by type or status), or work-log sessions. Examples: 'how many open "
            "issues', 'list all bugs', 'show the decisions', 'which sessions "
            "changed behavior'."
        ),
    )
    semantic_tool = QueryEngineTool.from_defaults(
        query_engine=SemanticQueryEngine(),
        name="semantic_search",
        description=(
            "Open-ended or explanatory questions about the project — why a "
            "decision was made, how something works, summaries, or anything that "
            "needs reasoning over the document text."
        ),
    )
    return RouterQueryEngine.from_defaults(
        selector=PydanticSingleSelector.from_defaults(llm=router_llm),
        query_engine_tools=[structured_tool, semantic_tool],
    )
