from config import pincone_vector_store, COHERE_API_KEY, EMBED_MODEL, GEMINI_API_KEY, LLM_MODEL
from llama_index.core import VectorStoreIndex, get_response_synthesizer
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.postprocessor.cohere_rerank import CohereRerank
from ui import build_app
from workflows import (
    Workflow,
    Context,
    step,
)
from workflows.events import (
    StartEvent,
    StopEvent,
    Event,
)
class QueryStartEvent(StartEvent):
    user_query: str

class RetrievedEvent(Event):
    candidates: list

class RerankedEvent(Event):
    nodes: list

class NoResultsEvent(Event):
    error_message: str



class RAGWorkflow(Workflow):
    def __init__(self, candidate_k=20, top_k=5, **kwargs):
        super().__init__(**kwargs)
        embed_model = CohereEmbedding(
        api_key=COHERE_API_KEY,
        model_name=EMBED_MODEL,
        input_type="search_query",
        )
        index = VectorStoreIndex.from_vector_store(pincone_vector_store, embed_model=embed_model)
        self.retriever = index.as_retriever(similarity_top_k=candidate_k)
        self.reranker = CohereRerank(api_key=COHERE_API_KEY, model="rerank-english-v3.0", top_n=top_k)
        llm = GoogleGenAI(api_key=GEMINI_API_KEY, model=LLM_MODEL)
        self.synthesizer = get_response_synthesizer(llm=llm, response_mode=ResponseMode.COMPACT)

    @step
    async def retrieval(self, ctx:Context, ev:QueryStartEvent) -> RetrievedEvent:
        await ctx.store.set("user_query", ev.user_query)
        candidates = self.retriever.retrieve(ev.user_query)
        return RetrievedEvent(candidates=candidates)
    
    @step
    async def rerank(self, ctx:Context, ev:RetrievedEvent) -> RerankedEvent:
        user_query = await ctx.store.get("user_query")
        nodes = self.reranker.postprocess_nodes(ev.candidates, query_str=user_query)
        return RerankedEvent(nodes=nodes)

    @step
    async def synthesize(self, ctx:Context, ev:RerankedEvent) -> StopEvent:
        user_query = await ctx.store.get("user_query")
        response = await self.synthesizer.asynthesize(user_query, ev.nodes)
        return StopEvent(result=response)


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


def make_chat(workflow):
    async def chat(message, history):
        response = await workflow.run(user_query=message)                              # retrieve + rerank
        return (
            f"{response.response}\n\n"
            f"---\n\n"
            f"<details><summary>📄 Sources</summary>\n\n"
            f"{format_sources(response.source_nodes)}\n\n</details>"
        )

    return chat


if __name__ == "__main__":
    workflow = RAGWorkflow(timeout=60)
    build_app(make_chat(workflow)).launch()  # UI gets a ready chat fn; it's retrieval-agnostic
