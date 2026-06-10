# Decisions

Important decisions made on this project, with rationale. Newest entries at the
top.

---

## Decision 5 - Handle files in memory, not on disk

**Date:** 2026-06-08

**Decision:** Read uploaded files and build output files using `io.BytesIO` rather
than writing temporary files to disk.

**Why:** Streamlit's `file_uploader` already gives an in-memory file-like object,
and `python-docx` can read/write file-like objects directly. Avoiding disk I/O
keeps the app simpler, avoids temp-file cleanup, and sidesteps OS/permission
issues.

---

## Decision 4 - Preserve plain text only, not formatting

**Date:** 2026-06-08

**Decision:** The MVP extracts and regenerates only the **plain text** of each
paragraph. Bold text, fonts, styles, tables, and images are not preserved.

**Why:** Preserving full DOCX formatting is significantly more complex because it
requires walking and rebuilding the document's XML structure. That complexity is
out of scope for a preparation project whose real purpose is to set up for a
later RAG system. Plain text is also the content a basic RAG pipeline is most
likely to need first.

**Trade-off / future work:** If formatting preservation becomes necessary, revisit
by editing runs in-place on the original document instead of rebuilding from
plain text.

---

## Decision 3 - Split DOCX logic from UI

**Date:** 2026-06-08

**Decision:** Put all DOCX read/write logic in `docx_utils.py` with **no Streamlit
imports**, and keep `app.py` for UI only.

**Why:** The future RAG system will likely reuse the DOCX I/O logic but not the
Streamlit UI. Keeping them separate makes that reuse clean and keeps each file
easy to test and reason about.

---

## Decision 2 - One paragraph per line as the editing model

**Date:** 2026-06-08

**Decision:** Join extracted paragraphs with newlines into a single text area; on
generation, split the edited text back into paragraphs by newline.

**Why:** It is the simplest editing model that maps cleanly onto the DOCX
paragraph structure. It is intuitive for the user and simple to implement. Empty
lines are kept as empty paragraphs to preserve spacing intent.

---

## Decision 1 - Streamlit and python-docx as the stack

**Date:** 2026-06-08

**Decision:** Build the MVP with Streamlit for the UI and python-docx for DOCX
I/O in Python.

**Why:** This stack was specified for the project. Streamlit gives a working web
UI with little boilerplate, and python-docx is a standard Python library for
`.docx` files. Both fit a small preparation project.
