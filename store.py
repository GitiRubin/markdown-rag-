"""Read + query layer for the extracted structured data.

The write path (extract.py) produces structured_data.json. This module is the
read path: load that JSON back into validated Pydantic objects and answer the
structured questions semantic search can't — filter by status/type, count, sort.
No LLM here; cheap and run-often.

`load()` is cached (lru_cache), so the file is read and validated once per run no
matter how many queries call it. Callers just import a query and call it — they
don't load or pass the data around.
"""

from collections import Counter
from functools import lru_cache
from pathlib import Path

from config import STRUCTURED_DATA_PATH
from schemas import ExtractedData, Decision, Issue, WorkLogEntry


@lru_cache(maxsize=1)
def load() -> ExtractedData:
    """Load structured_data.json once, re-validated into typed Pydantic objects."""
    text = Path(STRUCTURED_DATA_PATH).read_text(encoding="utf-8")
    return ExtractedData.model_validate_json(text)


# --- Issue queries ---------------------------------------------------------

def issues_by_status(status: str) -> list[Issue]:
    return [i for i in load().issues if i.status == status]


def issues_by_type(type_: str) -> list[Issue]:
    return [i for i in load().issues if i.type == type_]


def count_issues_by_type() -> dict[str, int]:
    return dict(Counter(i.type for i in load().issues))


# --- Decision queries ------------------------------------------------------

def decisions_sorted(newest_first: bool = True) -> list[Decision]:
    return sorted(load().decisions, key=lambda d: d.date or "", reverse=newest_first)


# --- Work-log queries ------------------------------------------------------

def work_log_sorted(newest_first: bool = True) -> list[WorkLogEntry]:
    return sorted(load().work_log, key=lambda w: w.date or "", reverse=newest_first)


def behavior_changes() -> list[WorkLogEntry]:
    """Sessions that changed app/source behavior."""
    return [w for w in load().work_log if w.changed_behavior]


# --- Cross-category --------------------------------------------------------

def by_source_file(file_name: str) -> ExtractedData:
    """Everything that came from one markdown file."""
    data = load()
    return ExtractedData(
        decisions=[d for d in data.decisions if file_name in d.source_files],
        issues=[i for i in data.issues if file_name in i.source_files],
        work_log=[w for w in data.work_log if file_name in w.source_files],
    )


if __name__ == "__main__":
    data = load()
    print(f"{len(data.decisions)} decisions, {len(data.issues)} issues, "
          f"{len(data.work_log)} log entries\n")
    print("issues by type:", count_issues_by_type())
    print("open issues:", [i.title for i in issues_by_status("open")])
    print("decisions (newest first):", [d.id for d in decisions_sorted()])
    print("work log (newest first):", [w.title for w in work_log_sorted()])
    print("behavior changes:", [w.title for w in behavior_changes()])
