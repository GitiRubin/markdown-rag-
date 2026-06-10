# CLAUDE.md

Guidance for Claude Code and humans working in this repository.

## What this project is

**Resume Formatter Assistant** - a minimal MVP: upload a `.docx`, extract its text,
edit it, and generate a new `.docx`.

This is a **preparation project**. The real goal is a later RAG system. Therefore:

- **Keep it small.** Resist adding features that are not part of the core
  upload -> edit -> download loop.
- **Favor clarity over cleverness.** This codebase is meant to be easy to read and
  build on later.
- **Document decisions.** Anything non-obvious goes in `docs/decisions.md`.

## Tech Stack

- Python 3.9+
- Streamlit for the UI
- python-docx for DOCX read/write

## Architecture

Two modules are intentionally separated:

- `docx_utils.py` - pure functions for DOCX I/O. No Streamlit imports here, so
  this logic stays reusable for the future RAG system.
- `app.py` - the Streamlit UI. Calls into `docx_utils` and holds UI/state logic.

This separation matters: the future RAG system will likely reuse `docx_utils` but
discard the Streamlit layer.

## Conventions

- Run the app with `streamlit run app.py`.
- DOCX content is handled in memory via `io.BytesIO`; no temp files on disk.
- Paragraph text is the unit of editing. One paragraph per line in the editor.

## Documentation Workflow

When you make a meaningful change:

1. Append a dated entry to `docs/work-log.md`.
2. If you made a design choice, record it in `docs/decisions.md`.
3. If you fixed a bug, record it in `docs/bugs-and-fixes.md`.
4. If tool responsibilities or review findings changed, update the relevant docs
   in `docs/`.

See `AGENTS.md` for repository-wide agent instructions.

## Known Limitations

Formatting is **not** preserved - only plain paragraph text. This is intentional
for the MVP. See `docs/decisions.md` (Decision 4).
