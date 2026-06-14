# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This is a [uv](https://docs.astral.sh/uv/)-managed Python 3.13 project.

- `uv sync` — install/lock dependencies from `pyproject.toml`
- `uv run ingest.py` — run the ingestion pipeline (loads, chunks, embeds, and upserts documents into Pinecone)
- `uv run main.py` — launch the Gradio retrieval UI (two-stage search over the indexed corpus)
- `uv add <package>` — add a dependency

There is no test suite, linter, or build step configured yet.

## Architecture

A RAG (retrieval-augmented generation) project built on **LlamaIndex**, embeddings + reranking from **Cohere**, answer synthesis from **Google Gemini**, a **Pinecone** vector store, and a **Gradio** chat UI. Both the ingestion and the full retrieve → rerank → synthesize sides exist.

**`config.py` — shared configuration and clients.** Imported by both `ingest.py` and `main.py`. Loads secrets from `.env`, defines constants (`INDEX_NAME="rag"`, `EMBED_MODEL="embed-english-v3.0"`, `NAMESPACE="resume_formatter"`, `LLM_MODEL="gemini-2.5-flash"`), and constructs the shared Pinecone client, index handle, and `PineconeVectorStore` once so they are created in a single place. It also calls `unstrict_ssl()` at the top of the module (see Network note) — because every other module imports from `config`, this runs before any network client is built.

**`ingest.py` — ingestion pipeline.** Runs top-to-bottom as a script (no functions). Stages:
1. **Load** — `SimpleDirectoryReader` reads every file in `md_files/`.
2. **Chunk** — `MarkdownNodeParser` splits along markdown structure (one node per section), then `SentenceSplitter` (chunk_size=256, overlap=40) caps oversized sections.
3. **Embed** — `CohereEmbedding` with `input_type="search_document"`.
4. **Index** — upserts into the Pinecone index/namespace via the shared `PineconeVectorStore` (from `config`) + `VectorStoreIndex.from_documents`.

**`main.py` — retrieval + synthesis side + UI entry point.** Three-stage flow:
1. **Retrieve** (`build_search`) — reconnects to the existing Pinecone store read-only (`VectorStoreIndex.from_vector_store`, no re-ingestion) and pulls a wide candidate set (`similarity_top_k=candidate_k`, default 20) by embedding similarity. The query embedding uses `input_type="search_query"` to match the `"search_document"` used at ingestion.
2. **Rerank** (`build_search`) — `CohereRerank` (`rerank-english-v3.0`) reorders candidates by true query-relevance and keeps the best `top_k` (default 5).
3. **Synthesize** (`build_synthesizer`) — a `GoogleGenAI` LLM (`LLM_MODEL`) plus `get_response_synthesizer(response_mode=COMPACT)` turns the reranked nodes + the query into a grounded natural-language answer. COMPACT packs the few small reranked chunks into a single LLM prompt, so synthesis is one call.

`make_chat(search, synthesizer)` wraps the two into a Gradio chat callback: it retrieves+reranks (`search`), synthesizes an answer (`synthesizer.synthesize(query, nodes)`), and renders the answer with the source passages (`format_sources`) tucked under a collapsible `<details>`. At startup, `search` and `synthesizer` are each built once and handed to `build_app(...).launch()`.

**`ui.py` — presentation only.** Defines the Gradio theme, CSS, header, and examples. `build_app(chat_fn)` takes a ready chat function with signature `fn(message, history) -> str` and wires it into a `gr.ChatInterface`. It knows nothing about retrieval — the retrieval logic in `main.py` and the UI are decoupled.

**`md_files/`** — the source corpus being indexed (markdown docs).

## Environment

Secrets are loaded from a `.env` file (gitignored) via `python-dotenv` in `config.py`. Required variables — `config.py` will `KeyError` if any is missing:
- `COHERE_API_KEY`
- `PINECONE_API_KEY`
- `GEMINI_API_KEY`

The Pinecone `NAMESPACE` and the Gemini `LLM_MODEL` are not read from the environment; they are constants in `config.py`.

## Network note

`config.py` calls `unstrict_ssl()` from `netfree-unstrict-ssl` at module top to relax SSL verification behind the NetFree content filter, before any network/API client is constructed. Because `ingest.py` and `main.py` both import from `config`, this runs first regardless of entry point. Keep the `unstrict_ssl()` call at the top of `config.py`, or HTTPS requests to Cohere/Pinecone/Google will fail.
