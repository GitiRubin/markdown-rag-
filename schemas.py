from typing import Literal
from pydantic import BaseModel, Field


class Decision(BaseModel):
    """A design/engineering decision recorded with its rationale."""

    id: str = Field(description="Decision identifier as written, e.g. 'Decision 4'. Empty string if none.")
    date: str | None = Field(default=None, description="ISO date (YYYY-MM-DD) the decision was made, or null if absent.")
    title: str = Field(description="Short title of the decision.")
    decision: str = Field(description="What was decided, in one or two sentences.")
    rationale: str | None = Field(default=None, description="Why it was decided (the 'Why' text), or null.")
    trade_off: str | None = Field(default=None, description="Stated trade-off or future-work note, or null.")
    status: Literal["active", "superseded"] = Field(default="active", description="'superseded' only if the text says it was replaced; otherwise 'active'.")
    source_files: list[str] = Field(default_factory=list, description="Source markdown file(s); left empty by the LLM, set by the pipeline and unioned across duplicates during dedup.")


class Issue(BaseModel):
    """A bug, limitation, risk, edge case, or future concern."""

    title: str = Field(description="Short title of the issue.")
    type: Literal["bug", "limitation", "risk", "edge_case", "future_concern"] = Field(
        description="Classification: 'bug' = something that actually broke; the others are non-events identified by review."
    )
    status: Literal["resolved", "open", "accepted"] = Field(
        description="'resolved' = fixed; 'accepted' = a deliberate, accepted trade-off; 'open' = known but unaddressed."
    )
    description: str = Field(description="What the issue is. For a fixed bug, the symptom/cause.")
    resolution: str | None = Field(default=None, description="How it was fixed or mitigated, or null if unresolved.")
    component: str | None = Field(default=None, description="File or module involved, e.g. 'docx_utils.py', or null.")
    date: str | None = Field(default=None, description="ISO date (YYYY-MM-DD) if recorded, else null.")
    source_files: list[str] = Field(default_factory=list, description="Source markdown file(s); left empty by the LLM, set by the pipeline and unioned across duplicates during dedup.")


class WorkLogEntry(BaseModel):
    """A dated work session from the chronological log."""

    date: str = Field(description="ISO date (YYYY-MM-DD) of the session.")
    title: str = Field(description="Short title of the session.")
    summary: str = Field(description="What was done, condensed from the bullet points.")
    status: str | None = Field(default=None, description="The 'Status:' line for the session, or null.")
    changed_behavior: bool = Field(
        default=False, description="True only if the entry says app/source behavior changed; the logs often note no behavior changed."
    )
    source_files: list[str] = Field(default_factory=list, description="Source markdown file(s); left empty by the LLM, set by the pipeline and unioned across duplicates during dedup.")


class ExtractedData(BaseModel):
    """Everything extracted from a single markdown file. All lists may be empty."""

    decisions: list[Decision] = Field(default_factory=list, description="Decisions found in the file, if any.")
    issues: list[Issue] = Field(default_factory=list, description="Issues found in the file, if any.")
    work_log: list[WorkLogEntry] = Field(default_factory=list, description="Work-log entries found in the file, if any.")
