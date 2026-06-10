# Resume Formatter Assistant

A minimal MVP that lets you upload a Word document (`.docx`), edit its text in the
browser, and download a freshly generated `.docx` file.

> **Note:** This project is intentionally small. It is a preparation project: a
> stepping stone toward a later, larger RAG (Retrieval-Augmented Generation)
> system. The focus here is a clean, working DOCX upload -> edit -> download loop
> and useful Markdown documentation for future project memory.

## Features

- Upload a `.docx` file
- Extract its text, paragraph by paragraph
- Edit the text directly in the browser
- Generate and download a new `.docx` file

## Tech Stack

- [Python](https://www.python.org/) 3.9+
- [Streamlit](https://streamlit.io/) - the web UI
- [python-docx](https://python-docx.readthedocs.io/) - reading and writing `.docx`

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run app.py
```

Streamlit will open the app in your browser, usually at <http://localhost:8501>.

## How to Use

1. Click **Browse files** and select a `.docx` file.
2. The document text appears in an editable text area, one paragraph per line.
3. Edit the text however you like.
4. Click **Generate DOCX** and then **Download** to save the new file.

## Project Structure

```text
resume-formatter-prep/
|-- AGENTS.md              # Repository instructions for AI agents
|-- app.py                 # Streamlit application
|-- docx_utils.py          # DOCX read/write helpers
|-- requirements.txt       # Python dependencies
|-- README.md              # Project overview and setup
|-- CLAUDE.md              # Claude Code guidance
`-- docs/
    |-- bugs-and-fixes.md  # Bugs encountered and how they were fixed
    |-- codex-review.md    # Codex review of current implementation
    |-- decisions.md       # Important decisions and their rationale
    |-- tool-comparison.md # Claude Code and Codex CLI roles
    `-- work-log.md        # Chronological log of work done
```

## Limitations

This MVP keeps only the **plain text** of each paragraph. Rich formatting such as
bold text, fonts, tables, images, and styles is **not** preserved.

That trade-off is intentional for this preparation phase. See `docs/decisions.md`.
