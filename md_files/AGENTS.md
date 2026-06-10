# AGENTS.md

Repository instructions for AI coding agents and human contributors.

## Project Goal

Resume Formatter Assistant is a small preparation project for a later RAG
(Retrieval-Augmented Generation) system.

The near-term goal is to keep a simple DOCX upload, plain-text edit, and DOCX
download loop working while producing clear Markdown documentation that can later
be indexed by a RAG pipeline.

## MVP Scope

The MVP includes only:

- Upload a `.docx` file.
- Extract document paragraph text.
- Show the extracted text in a browser editor.
- Generate and download a new `.docx` from the edited plain text.

The MVP explicitly does not include:

- Formatting preservation.
- Tables, images, headers, footers, comments, tracked changes, or style handling.
- Authentication, persistence, user accounts, databases, or background jobs.
- LLM calls, embeddings, vector search, or RAG features.

## Tech Stack

- Python 3.9+
- Streamlit for the web UI
- python-docx for DOCX input and output
- Markdown for project knowledge capture

## Coding Rules

- Keep the project small and easy to inspect.
- Do not add new app features unless they are explicitly requested.
- Keep DOCX logic in `docx_utils.py` and UI logic in `app.py`.
- Do not import Streamlit from `docx_utils.py`.
- Prefer pure functions for reusable document-processing logic.
- Keep files in memory with `io.BytesIO`; avoid temporary files unless there is a
  clear reason.
- Do not install new packages without an explicit need and documentation update.
- Avoid broad refactors. Make the smallest change that satisfies the task.
- Preserve the plain-text paragraph model unless the project scope changes.

## Documentation Rules

- Treat Markdown files as first-class project artifacts.
- Keep documentation concise, factual, and useful for a future RAG system.
- Prefer stable headings and short sections over long narrative text.
- Use plain ASCII punctuation where practical to avoid encoding issues.
- Record important design decisions in `docs/decisions.md`.
- Record bug discoveries and fixes in `docs/bugs-and-fixes.md`.
- Record meaningful work sessions in `docs/work-log.md`.
- Keep tool roles and agent responsibilities documented in `docs/tool-comparison.md`.
- Keep project reviews and known risks documented in `docs/codex-review.md`.

## Required Documentation Update

Every meaningful change must update Markdown documentation in the same session.

Examples of meaningful changes:

- Source code behavior changes.
- Dependency changes.
- Project structure changes.
- Bug fixes.
- New constraints or decisions.
- New review findings that affect future work.

If a change does not require a documentation update, the final response should say
why.
