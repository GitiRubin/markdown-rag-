# Work Log

A chronological log of work done on this project. Newest entries at the top.

---

## 2026-06-08 - Expanded issue classification

- Reviewed `docs/bugs-and-fixes.md` for realistic project issues.
- Reclassified non-event items as `Limitation`, `Risk`, `Edge Case`, or
  `Future Concern`.
- Added additional realistic concerns for empty documents, large documents,
  missing tests, missing `.gitignore`, resume privacy, Unicode/bidirectional text,
  and future RAG chunk boundaries.
- Did not invent new bug events and did not change app behavior.

**Status:** Issue tracking is clearer for future RAG-oriented review.

---

## 2026-06-08 - Bug and limitation review

- Reviewed the current code (`app.py`, `docx_utils.py`) and the development
  process so far.
- Updated `docs/bugs-and-fixes.md` with the actual issues encountered:
  - `ModuleNotFoundError: No module named 'docx'` before installing dependencies.
  - `pip install` moving to a background task.
  - Hebrew project path (`תכנות`) rendering as garbled text in the console.
- Added a "Potential Issues and Limitations" section covering real, code-level
  risks: `\n`-only newline handling, top-level-paragraphs-only extraction, no
  error handling for bad files, no legacy `.doc` support, plain-text-only round
  trip, trailing empty paragraph, and the fixed output filename.
- No invented bugs; no app behavior changed.

**Status:** Bug and limitation tracking is current.

---

## 2026-06-08 - Codex documentation review

- Reviewed the existing Python implementation and Markdown documentation.
- Added `AGENTS.md` with project goal, MVP scope, tech stack, coding rules, and
  documentation rules.
- Added `docs/tool-comparison.md` to clarify Claude Code and Codex CLI roles.
- Added `docs/codex-review.md` with current files, implementation summary, risks,
  and next steps.
- Lightly cleaned `README.md` and `CLAUDE.md` to remove encoding-sensitive
  punctuation and reflect the new documentation files.
- Did not change app behavior, refactor Python code, or install packages.

**Status:** Documentation improved for future RAG-oriented project memory.

---

## 2026-06-08 - Initial MVP scaffold

- Created project documentation:
  - `README.md` - overview, setup, usage.
  - `CLAUDE.md` - guidance for AI assistants / contributors.
  - `docs/work-log.md` - this file.
  - `docs/decisions.md` - design decisions and rationale.
  - `docs/bugs-and-fixes.md` - bug tracker.
- Created `requirements.txt` (streamlit, python-docx).
- Implemented `docx_utils.py`:
  - `extract_paragraphs(file)` - read paragraph text from an uploaded `.docx`.
  - `build_docx(text)` - build a new `.docx` (in-memory `BytesIO`) from edited text.
- Implemented `app.py` - Streamlit UI wiring upload -> edit -> download.

**Status:** Core MVP loop complete. Ready to run with `streamlit run app.py`.
