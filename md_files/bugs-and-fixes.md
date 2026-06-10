# Bugs and Fixes

A log of bugs encountered and how they were fixed. Newest entries at the top.

---

## 2026-06-08 - python-docx not installed when running the smoke test

**Symptom:** The first round-trip smoke test failed immediately with:

```text
ModuleNotFoundError: No module named 'docx'
```

**Cause:** `docx_utils.py` imports `from docx import Document`, but the
dependencies in `requirements.txt` (`python-docx`) had not been installed in the
environment yet. The code was written before the packages were present.

**Fix:** Ran `pip install -r requirements.txt`, confirmed `python-docx` was
installed, then re-ran the smoke test. The round trip then passed: extracting from
a generated `.docx` and rebuilding from edited text both returned the expected
paragraphs.

**Note:** The package is imported as `docx` but installed as `python-docx`. This
name mismatch is a common source of confusion and is worth remembering for the
future RAG project.

---

## 2026-06-08 - pip install exceeded the foreground command window

**Symptom:** `pip install -r requirements.txt` did not return within the normal
foreground command limit and was moved to a background task.

**Cause:** Downloading and installing Streamlit and its transitive dependencies
takes longer than a quick command. This is expected behavior, not a defect.

**Fix:** Let the install finish in the background, then verified completion
(`pip show python-docx`) before continuing. No code change required.

---

## 2026-06-08 - Hebrew project path rendered as garbled text in the console

**Symptom:** In the failing traceback, the project path
`C:\Users\...\Documents\תכנות\resume-formatter-prep` displayed as
`C:\Users\...\Documents\?????\resume-formatter-prep`.

**Cause:** The project lives under a directory whose name contains Hebrew
characters (`תכנות`). The Windows console code page does not render those
characters, so they show as replacement glyphs in stderr output.

**Fix / mitigation:** No fix needed for current functionality. The garbling is a
display-only artifact; Python and python-docx handled the path correctly and the
app runs. Flagged here because other tools invoked from this path could hit real
encoding issues, and the non-ASCII path is the first thing to check if they do.

---

## Potential Issues, Risks, Edge Cases, and Future Concerns

These are not bugs that occurred, but real risks and design limits identified by
reviewing the code and the recorded decisions. They are documented so the future
RAG project does not rediscover them the hard way.

### Edge Case - Newline handling assumes `\n` only

`build_docx` splits the edited text with `text.split("\n")`. On Windows, uploaded
or pasted content can use `\r\n` line endings. If a stray `\r` survives in the
text area, it can be carried into paragraph text. Mitigation for later: normalize
line endings (for example `text.replace("\r\n", "\n").replace("\r", "\n")`) before
splitting.

### Limitation - Only top-level paragraphs are extracted

`extract_paragraphs` reads `document.paragraphs` only. Text inside **tables,
headers, and footers is silently dropped**. Many resumes use tables for layout, so
a user could upload a document and find content missing from the editor with no
warning. This is a known scope limit of the MVP; the future system should walk
tables and section parts if full extraction is required.

### Edge Case - Empty documents produce an empty editor

If a valid `.docx` contains no top-level paragraph text, the app will show an empty
text area. That may be correct for a truly empty document, but it may also mean the
content lives in tables, headers, footers, text boxes, or other document parts not
currently extracted. A future version could distinguish "empty document" from
"unsupported content locations."

### Risk - No error handling for corrupt or non-DOCX files

The uploader restricts selection to `.docx`, but a renamed, corrupt, or
password-protected file would still reach `Document(file)` and raise an unhandled
exception, surfacing as a raw Streamlit traceback rather than a friendly message.
Mitigation for later: wrap extraction in `try/except` and show `st.error(...)`.

### Limitation - Legacy `.doc` is not supported

`python-docx` reads only the Office Open XML `.docx` format, not the older binary
`.doc`. The file-type filter (`type=["docx"]`) currently masks this, but it is a
hard limitation of the library, not a temporary gap.

### Limitation - Plain-text-only round trip loses formatting

By design (see `docs/decisions.md`, Decision 4), only paragraph text is preserved.
Bold, fonts, styles, tables, and images are lost on regeneration. This is an
accepted trade-off for the MVP, but it means the output is not a faithful copy of
the input and should not be presented as one.

### Edge Case - A trailing newline produces an extra empty paragraph

Because `build_docx` always splits on every `\n`, text ending in a newline yields a
trailing empty paragraph in the generated document. Harmless today, but a thing to
be aware of if exact paragraph counts ever matter.

### Limitation - Output filename is fixed

The generated file is always named `formatted_resume.docx` regardless of the input
filename. Not a bug, but a small UX limitation worth revisiting.

### Risk - Large documents may make the Streamlit editor awkward

The app loads all extracted text into one `st.text_area`. This is fine for a resume
MVP, but a large document could become slow or uncomfortable to edit. A future RAG
system may also need chunking, pagination, or section-level processing instead of
one large text field.

### Future Concern - No automated test coverage

There are no committed automated tests for `extract_paragraphs` or `build_docx`.
This is acceptable for the tiny MVP, but future changes to extraction behavior
should add tests with small generated `.docx` fixtures so paragraph handling does
not regress silently.

### Future Concern - No `.gitignore` yet

The folder currently contains `__pycache__/`, which is generated bytecode and not
source. If this project becomes a Git repository, add a `.gitignore` before
committing so cache files, virtual environments, and local output documents are not
tracked accidentally.

### Risk - Uploaded resume content is sensitive

Resumes can contain personal data such as names, phone numbers, email addresses,
employment history, and addresses. The current app handles files in memory and
does not persist them, which is good for the MVP. If later work adds logging,
storage, LLM calls, or RAG indexing, privacy rules must be documented before data
leaves the local process.

### Edge Case - Unicode and bidirectional text may need explicit validation

The project path already exposed console encoding quirks, and resumes may contain
Hebrew, Arabic, accented Latin characters, symbols, or mixed left-to-right and
right-to-left text. `python-docx` can handle Unicode text, but future extraction,
display, chunking, or retrieval steps should be checked with multilingual samples.

### Future Concern - RAG chunk boundaries may not match DOCX paragraphs

The MVP uses one DOCX paragraph per editor line. That is a good editing model, but
it may not be the right retrieval model for a future RAG system. Later RAG work
should define chunking rules separately instead of assuming that DOCX paragraphs
are always useful retrieval chunks.
