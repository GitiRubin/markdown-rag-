"""Data Extraction stage: pull structured records from md_files/ into JSON.

Unified extraction — each whole markdown file is sent to the LLM once and asked
to fill `ExtractedData` (all categories at once). Empty lists are valid. Every
returned record is stamped with its source file, then the per-file results are
merged and written to `structured_data.json`. Run with `uv run extract.py`.

Calls are throttled and retried: we space requests and back off on transient
429 (rate limit) / 503 errors.
"""

import time
from pathlib import Path
from llama_index.core import PromptTemplate

from config import llm, STRUCTURED_DATA_PATH
from schemas import ExtractedData
from dedupe import dedupe_issues

MD_DIR = Path("md_files")

REQUEST_INTERVAL = 13   # seconds between calls — stays under the 5 req/min free-tier limit
MAX_RETRIES = 4
BACKOFF = 30            # seconds to wait before retrying a throttled/unavailable call

PROMPT = PromptTemplate(
    "You are extracting structured project memory from a markdown document.\n"
    "Extract every Decision, Issue, and WorkLogEntry that this document DESCRIBES "
    "in its own right. Rules:\n"
    "- Return empty lists for any category that is not present.\n"
    "- Extract an item when the document itself describes it — gives its details, "
    "symptom, rationale, or a dedicated entry/section. This INCLUDES spelled-out "
    "lists of risks, limitations, edge cases, and future concerns, even if they "
    "are framed as potential rather than things that already happened.\n"
    "- Do NOT extract an item that is only mentioned in passing or as a reference "
    "to another document (e.g. a work-log entry saying it 'reviewed the bug "
    "tracker' or 'added concerns about X' without describing them here).\n"
    "- Do NOT invent, infer, or duplicate records beyond what the text states.\n"
    "- Leave source_files empty; the pipeline sets it.\n\n"
    "Document:\n{document}"
)

# bind the shared LLM to the schema once: .complete() now returns a validated object
structured_llm = llm.as_structured_llm(ExtractedData)


def _complete_with_retry(prompt: str) -> ExtractedData:
    """Call the structured LLM, retrying transient 429/503 errors with backoff."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return structured_llm.complete(prompt).raw
        except Exception as e:
            transient = "429" in str(e) or "503" in str(e)
            if not transient or attempt == MAX_RETRIES:
                raise
            print(f"    transient error (attempt {attempt}/{MAX_RETRIES}); waiting {BACKOFF}s")
            time.sleep(BACKOFF)


def _drop_empty(data: ExtractedData) -> None:
    """Remove junk records the LLM sometimes emits (e.g. a blank decision)."""
    data.decisions = [d for d in data.decisions if d.title.strip()]
    data.issues = [i for i in data.issues if i.title.strip()]
    data.work_log = [w for w in data.work_log if w.title.strip()]


def extract_file(path: Path) -> ExtractedData:
    """Run unified extraction on one file and stamp source_files on every record."""
    text = path.read_text(encoding="utf-8")
    data = _complete_with_retry(PROMPT.format(document=text))
    _drop_empty(data)
    for record in (*data.decisions, *data.issues, *data.work_log):
        record.source_files = [path.name]
    return data


def main() -> None:
    merged = ExtractedData()
    files = sorted(MD_DIR.glob("*.md"))
    for n, path in enumerate(files):
        if n:
            time.sleep(REQUEST_INTERVAL)            # throttle to respect the rate limit
        try:
            data = extract_file(path)
        except Exception as e:                      # keep the run alive; report the file
            print(f"  ! {path.name} failed: {e}")
            continue
        merged.decisions.extend(data.decisions)
        merged.issues.extend(data.issues)
        merged.work_log.extend(data.work_log)
        print(f"  {path.name}: {len(data.decisions)} decisions, "
              f"{len(data.issues)} issues, {len(data.work_log)} log entries")

    # dedup: the same issue is often recorded in several files; collapse near-dups.
    before = len(merged.issues)
    try:
        time.sleep(REQUEST_INTERVAL)            # respect the rate limit before the dedup call
        merged.issues = dedupe_issues(merged.issues)
        print(f"\n  deduped issues: {before} -> {len(merged.issues)}")
    except Exception as e:                      # never lose extraction work on a dedup failure
        print(f"\n  ! dedup failed, writing un-deduped issues: {e}")

    Path(STRUCTURED_DATA_PATH).write_text(merged.model_dump_json(indent=2), encoding="utf-8")
    print(f"\nWrote {STRUCTURED_DATA_PATH}: {len(merged.decisions)} decisions, "
          f"{len(merged.issues)} issues, {len(merged.work_log)} log entries")


if __name__ == "__main__":
    main()
