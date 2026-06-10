# Tool Comparison: Claude Code and Codex CLI

This project may be worked on by both Claude Code and Codex CLI. Their roles
overlap, but the project benefits from keeping their responsibilities explicit.

## Shared Responsibilities

Both tools can:

- Read the repository and summarize current behavior.
- Edit Python and Markdown files.
- Run local commands when appropriate.
- Maintain the small MVP scope.
- Update Markdown documentation after meaningful changes.
- Identify risks, missing tests, and unclear decisions.

## Claude Code Role

Claude Code created the initial implementation and local project structure.

Best fit in this project:

- Fast scaffolding of the Streamlit MVP.
- Initial app wiring and helper module creation.
- Capturing early project decisions.
- Iterating on simple implementation tasks when the scope is clear.

Expected behavior:

- Keep the upload -> edit -> download loop simple.
- Avoid introducing RAG features before the preparation phase is complete.
- Update `CLAUDE.md`, `docs/work-log.md`, and other Markdown files when behavior
  changes.

## Codex CLI Role

Codex CLI is used here as a repository review and documentation agent.

Best fit in this project:

- Careful project inspection before changes.
- Documentation cleanup and structure for future RAG ingestion.
- Reviewing implementation risks without expanding scope.
- Maintaining `AGENTS.md`, `docs/codex-review.md`, and cross-agent guidance.

Expected behavior:

- Do not add new app features during documentation-only tasks.
- Do not refactor working code unless a critical issue is found.
- Keep Markdown factual, compact, and easy to retrieve.
- Record review findings and next steps for later sessions.

## Practical Workflow

1. Use Claude Code or Codex CLI to make a scoped change.
2. Keep code changes small and aligned with the MVP.
3. Update Markdown documentation in the same session.
4. Record decisions, bugs, and work-log entries in the appropriate files.
5. Use review documents to preserve context for future RAG work.

## Boundary for This Project

This repository is not yet the RAG system. It is a preparation project.

Neither tool should add embeddings, vector databases, LLM prompts, retrieval
pipelines, authentication, or persistence unless the project scope is explicitly
changed.
