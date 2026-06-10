from config import pincone_vector_store, COHERE_API_KEY, EMBED_MODEL
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.postprocessor.cohere_rerank import CohereRerank
from ui import build_app


def build_search(candidate_k=20, top_k=5):
    embed_model = CohereEmbedding(
        api_key=COHERE_API_KEY,
        model_name=EMBED_MODEL,
        input_type="search_query",
    )

    # Reconnect to the existing Pinecone store (read-only) — no re-ingestion.
    index = VectorStoreIndex.from_vector_store(pincone_vector_store, embed_model=embed_model)

    # Stage 1: pull a WIDE candidate set by embedding similarity (cheap, recall-focused).
    retriever = index.as_retriever(similarity_top_k=candidate_k)

    # Stage 2: a cross-encoder reranker reorders candidates by true query-relevance
    # and keeps only the best top_k (precision-focused).
    reranker = CohereRerank(api_key=COHERE_API_KEY, model="rerank-english-v3.0", top_n=top_k)

    def search(query):
        candidates = retriever.retrieve(query)
        return reranker.postprocess_nodes(candidates, query_str=query)

    return search


def format_sources(nodes):
    if not nodes:
        return "_No relevant passages found in the documents._"

    cards = []
    for i, n in enumerate(nodes, start=1):
        source = n.metadata.get("file_name", "unknown")
        relevance = f"{n.score:.0%}" if n.score is not None else "—"
        cards.append(
            f"**{i}. `{source}`** &nbsp;·&nbsp; relevance **{relevance}**\n\n"
            f"> {n.text.strip()}"
        )
    return "\n\n---\n\n".join(cards)


def make_chat(search):
    def chat(message, history):
        nodes = search(message)
        return format_sources(nodes)

    return chat


if __name__ == "__main__":
    search = build_search()                # built once, at startup
    build_app(make_chat(search)).launch()  # UI gets a ready chat fn; it's retrieval-agnostic
