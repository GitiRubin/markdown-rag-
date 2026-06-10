# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This is a [uv](https://docs.astral.sh/uv/)-managed Python 3.13 project.

- `uv sync` — install/lock dependencies from `pyproject.toml`
- `uv run prepare.py` — run the ingestion pipeline (loads, chunks, embeds, and upserts documents into Pinecone)
- `uv run main.py` — entry point (currently a placeholder)
- `uv add <package>` — add a dependency

There is no test suite, linter, or build step configured yet.

## Architecture

A RAG (retrieval-augmented generation) project built on **LlamaIndex**, embeddings from **Cohere**, and a **Pinecone** vector store. It is early-stage: only the ingestion side exists.

**`prepare.py` — ingestion pipeline.** Runs top-to-bottom as a script (no functions). Stages:
1. **Load** — `SimpleDirectoryReader` reads every file in `md_files/`.
2. **Chunk** — `MarkdownNodeParser` splits along markdown structure (one node per section), then `SentenceSplitter` (chunk_size=256, overlap=40) caps oversized sections.
3. **Embed** — `CohereEmbedding` with model `embed-english-v3.0` and `input_type="search_document"`.
4. **Index** — upserts into the Pinecone index named `rag` under the configured namespace via `PineconeVectorStore` + `VectorStoreIndex.from_documents`.

**`main.py`** — placeholder entry point; the query/retrieval side has not been written. When adding retrieval, the embedding query side must use `input_type="search_query"` to match the `"search_document"` used at ingestion.

**`md_files/`** — the source corpus being indexed (markdown docs).

## Environment

Secrets are loaded from a `.env` file (gitignored) via `python-dotenv`. Required variables — the scripts will `KeyError` if any are missing:
- `COHERE_API_KEY`
- `PINECONE_API_KEY`
- `NAMESPACE` — the Pinecone namespace to write/read

## Network note

`prepare.py` calls `unstrict_ssl()` from `netfree-unstrict-ssl` at startup to relax SSL verification behind the NetFree content filter. Keep this call before any network/API client is constructed, or HTTPS requests to Cohere/Pinecone will fail.
