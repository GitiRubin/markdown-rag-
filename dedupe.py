"""Deduplication pass for extracted records.

The same real-world item (an issue, usually) can be documented in more than one
markdown file with different wording, so the merged extraction holds near-dups.
This module collapses records describing the SAME underlying item into one
canonical record and unions their source files.

Conservative by design: it only selects among values already present in the
original records and copies them verbatim. It never paraphrases, invents, or
upgrades a type/status by severity or judgment. Records that genuinely conflict
are left unmerged rather than silently resolved. Runs at temperature 0.

Only `issues` are deduped today (decisions/work-log are clean, single-source);
`_dedupe` is category-generic so extending it later is a one-liner.
"""

import json
import time

from pydantic import BaseModel, Field
from llama_index.core import PromptTemplate
from llama_index.llms.google_genai import GoogleGenAI

from config import GEMINI_API_KEY, LLM_MODEL
from schemas import Issue

MAX_RETRIES = 4
BACKOFF = 30            # seconds before retrying a throttled/unavailable call

# temperature 0 — dedup must be as deterministic and literal as the API allows
dedup_llm = GoogleGenAI(api_key=GEMINI_API_KEY, model=LLM_MODEL, temperature=0)


class DedupedIssues(BaseModel):
    """Canonical issue list after duplicates are merged."""

    items: list[Issue] = Field(default_factory=list)


DEDUP_PROMPT = PromptTemplate(
    "You are deduplicating a list of extracted {category} from a software "
    "project's documentation. The same item is sometimes recorded in more than "
    "one source file with different wording.\n\n"
    "Collapse records that describe the SAME underlying item into one canonical "
    "record. Follow these STRICT rules:\n"
    "- Merge ONLY records describing the same underlying item. If two records are "
    "related or similar but distinct (e.g. a performance concern vs a separate UX "
    "concern), keep them separate.\n"
    "- Do NOT rewrite, paraphrase, summarize, or invent any field value. Copy "
    "field values VERBATIM from the originals.\n"
    "- When merging, for each field use the value from the richest / most explicit "
    "original (the one with the fullest description). Every value you output must "
    "appear verbatim in one of the merged originals.\n"
    "- NEVER upgrade or reinterpret 'type' or 'status' by severity or judgment. "
    "Only use a type/status value literally present in one of the merged records.\n"
    "- If two records appear to be the same item but have genuinely conflicting "
    "type/status and it is not clear which original is richer, DO NOT merge them.\n"
    "- Always UNION the source_files of merged records.\n"
    "- Never drop a non-duplicate. The output count must be <= the input count.\n\n"
    "Records (JSON):\n{records}"
)


def _dedupe(records: list, category: str, output_cls: type[BaseModel]) -> list:
    """Run one conservative dedup pass; returns the canonical list."""
    if len(records) <= 1:
        return records
    payload = json.dumps([r.model_dump() for r in records], ensure_ascii=False, indent=2)
    prompt = DEDUP_PROMPT.format(category=category, records=payload)
    structured = dedup_llm.as_structured_llm(output_cls)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return structured.complete(prompt).raw.items
        except Exception as e:
            transient = "429" in str(e) or "503" in str(e)
            if not transient or attempt == MAX_RETRIES:
                raise
            print(f"    transient error (attempt {attempt}/{MAX_RETRIES}); waiting {BACKOFF}s")
            time.sleep(BACKOFF)


def dedupe_issues(issues: list[Issue]) -> list[Issue]:
    """Merge near-duplicate issues recorded across multiple files."""
    return _dedupe(issues, "issues", DedupedIssues)
