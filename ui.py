# ui.py
# All presentation for the Docs Assistant chat: theme, CSS, layout, examples.
# Knows nothing about retrieval — build_app() takes a ready chat function
# (signature: fn(message, history) -> str) and wires it into the interface.
import gradio as gr

THEME = gr.themes.Default(
    primary_hue="indigo",
    secondary_hue="violet",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
)

CSS = """
.gradio-container { max-width: 880px !important; margin: 0 auto !important; }

/* Bold gradient banner instead of the pale centered text */
#header {
    text-align: center;
    padding: 22px 16px;
    margin-bottom: 10px;
    border-radius: 14px;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: #ffffff;
    box-shadow: 0 6px 18px rgba(79, 70, 229, 0.35);
}
#header h1 { margin: 0 0 4px; font-weight: 800; color: #ffffff; }
#header p { margin: 0; color: rgba(255, 255, 255, 0.92); font-weight: 500; }
footer { display: none !important; }

/* Shrink the retrieved-passage text, but keep it strong (not greyed out) */
.message-content, .message-content *,
.message, .message *,
.bubble, .bubble *,
.prose, .prose * {
    font-size: 0.82rem !important;
    line-height: 1.45 !important;
}

/* Vivid accent on the quoted passages instead of pale grey */
.message blockquote, .message-content blockquote, .prose blockquote {
    border-left: 3px solid #6366f1 !important;
    background: rgba(99, 102, 241, 0.07) !important;
    padding: 6px 12px !important;
    border-radius: 0 6px 6px 0 !important;
    color: var(--body-text-color) !important;
}

/* Make the primary (send) button pop */
button.primary, .primary { font-weight: 600 !important; }
"""

HEADER = """
<div id="header">
    <h1>📚 Docs Assistant</h1>
    <p>Ask questions about your Markdown documentation —
       answers are grounded in the indexed source files.</p>
</div>
"""

EXAMPLES = [
    "How many issues are there of each type?",          # structured: count
    "List the open issues.",                            # structured: filter by status
    "Why was plain text chosen instead of preserving formatting?",  # semantic
    "Summarize the key decisions that were made.",      # semantic
]


def build_app(chat_fn):
    with gr.Blocks(theme=THEME, css=CSS, title="Docs Assistant") as app:
        gr.HTML(HEADER)
        gr.ChatInterface(
            fn=chat_fn,
            examples=EXAMPLES,
            chatbot=gr.Chatbot(
                height=520,
                placeholder="Ask anything about your documents to get started.",
            ),
            textbox=gr.Textbox(
                placeholder="Type your question and press Enter…",
                container=False,
                scale=7,
            ),
        )
    return app
