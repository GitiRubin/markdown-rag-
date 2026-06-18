# RAG Agent over Project Documentation

A Retrieval-Augmented Generation agent that answers questions about a software
project's Markdown documentation. It combines two complementary ways of
answering, behind a single router:

- **Semantic search** — for open-ended, explanatory questions ("*why* was this
  decided?", "*how* does X work?"). Answered by embedding retrieval → reranking →
  LLM synthesis, grounded in the source passages.
- **Structured data** — for count / filter / list questions ("how many open
  issues?", "list all bugs", "show the decisions"). Answered **exactly** from a
  structured database extracted from the docs — no LLM guessing, fully
  reproducible, with provenance.

A LlamaIndex **RouterQueryEngine** inspects each question and sends it down the
right path automatically.

## Why both paths?

Semantic search is great for meaning but bad at precise aggregation — it can't
reliably answer "how many open issues are there?". Structured extraction turns
the docs into a queryable database that answers those exactly. The agent uses
each where it is strongest.

## Architecture

```
                          ┌─────────────────────────────┐
  question ──► Router ──► │ structured_data  (exact)     │ ──► answer
              (selector)  │   intent → store.py lookup   │
                          ├─────────────────────────────┤
                          │ semantic_search  (generative)│ ──► answer + sources
                          │   retrieve → rerank → retry  │
                          │   → synthesize (RAGWorkflow) │
                          └─────────────────────────────┘
```

**Two ingestion sides feed it:**

1. **Vector index** (`ingest.py`) — loads `md_files/`, chunks along Markdown
   structure, embeds with Cohere, upserts into Pinecone. Powers semantic search.
2. **Structured extraction** (`extract.py`) — an LLM extracts typed records
   (decisions, issues, work-log entries) from each file into
   `structured_data.json`, then a conservative LLM **dedup** pass merges the same
   item recorded across multiple files. Powers structured queries.

| File | Role |
|------|------|
| `config.py` | Shared secrets, constants, and clients (Pinecone, LLM). |
| `ingest.py` | Build the Pinecone vector index from `md_files/`. |
| `schemas.py` | Pydantic schemas for the extracted records. |
| `extract.py` | Extract structured records → `structured_data.json` (+ dedup). |
| `dedupe.py` | Conservative LLM deduplication of extracted issues. |
| `store.py` | Read/query layer over `structured_data.json` (filter, count, sort). |
| `router.py` | RouterQueryEngine: structured vs. semantic tools + intent classify. |
| `main.py` | The semantic `RAGWorkflow` + Gradio chat entry point. |
| `ui.py` | Gradio theme, layout, and examples (presentation only). |
| `md_files/` | The documentation corpus being indexed. |

## Tech stack

Python 3.13 · [uv](https://docs.astral.sh/uv/) · **LlamaIndex** (orchestration,
workflow, router) · **Cohere** (embeddings + reranking) · **OpenAI** (LLM:
extraction, dedup, routing, synthesis) · **Pinecone** (vector store) ·
**Gradio** (chat UI).

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```
2. Create a `.env` file with your API keys:
   ```env
   COHERE_API_KEY=...
   PINECONE_API_KEY=...
   OPENAI_API_KEY=...
   ```
   A Pinecone index named `rag` must exist (see `INDEX_NAME` in `config.py`).

## Running

Run the pipeline in order. The two build steps are independent and only need to
be re-run when `md_files/` changes.

```bash
# 1. Build the semantic vector index (one-time / when docs change)
uv run ingest.py

# 2. Extract the structured database (one-time / when docs change)
uv run extract.py

# 3. Launch the chat agent
uv run main.py
```

`main.py` opens a Gradio chat in the browser (usually http://localhost:7860).

## Example questions the agent can answer

**Structured** (exact answer from `structured_data.json`, no source passages):

- "How many issues are there of each type?" → a count breakdown by type.
- "List the open issues." → every issue with status `open`, plus its source file(s).
- "What bugs were recorded?" → all issues of type `bug`.
- "Show the project decisions, newest first." → the decision log.
- "Which work sessions changed the app's behavior?" → filtered work-log entries.
- "List the work-log sessions." → the full dated work log.

**Semantic** (synthesized answer grounded in retrieved passages, with a Sources
section):

- "Why was plain text chosen instead of preserving formatting?"
- "How is the DOCX logic separated from the UI, and why?"
- "What are the main risks if the project handles real resumes?"
- "Explain how files are handled in memory rather than on disk."

## Notes

- The embedding and reranking models are English (`embed-english-v3.0`,
  `rerank-english-v3.0`), so semantic questions work best in English. For
  cross-lingual questions, switch to Cohere's `*-multilingual-v3.0` models and
  re-run `ingest.py`.
- `extract.py` calls the LLM per file and runs a dedup pass; it is throttled and
  retries transient errors, so a full run takes a couple of minutes.
