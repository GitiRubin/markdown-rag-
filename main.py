from config import pincone_vector_store, COHERE_API_KEY, EMBED_MODEL, GEMINI_API_KEY, LLM_MODEL
from llama_index.core import VectorStoreIndex, get_response_synthesizer
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.postprocessor.cohere_rerank import CohereRerank
from ui import build_app
from workflows import Workflow, Context, step
from workflows.events import StartEvent, StopEvent, Event

# Routing thresholds — tune freely.
CONFIDENCE_THRESHOLD = 0.5   # min rerank score of the top node to trust the results
MAX_RETRIES = 2              # how many times we widen the search before giving up


# ---------- Events: each one is an edge in the flow graph ----------
class QueryStartEvent(StartEvent):
    user_query: str

class CleanQueryEvent(Event):      # validated + normalized query, ready to retrieve
    user_query: str

class RetrievedEvent(Event):       # raw candidate set from the vector store
    candidates: list

class RerankedEvent(Event):        # candidates reordered + trimmed by the reranker
    nodes: list

class SynthesizeEvent(Event):      # results passed confidence check → ready to answer
    nodes: list

class RetryEvent(Event):           # confidence too low → search again, wider
    reason: str

class NoResultsEvent(Event):       # nothing useful found → stop with a friendly message
    error_message: str


class RAGWorkflow(Workflow):
    def __init__(self, candidate_k=20, top_k=5, **kwargs):
        super().__init__(**kwargs)
        self.candidate_k = candidate_k
        embed_model = CohereEmbedding(
            api_key=COHERE_API_KEY,
            model_name=EMBED_MODEL,
            input_type="search_query",
        )
        # Keep the index itself — retry_search needs to build a wider retriever at runtime.
        self.index = VectorStoreIndex.from_vector_store(pincone_vector_store, embed_model=embed_model)
        self.retriever = self.index.as_retriever(similarity_top_k=candidate_k)
        self.reranker = CohereRerank(api_key=COHERE_API_KEY, model="rerank-english-v3.0", top_n=top_k)
        llm = GoogleGenAI(api_key=GEMINI_API_KEY, model=LLM_MODEL)
        self.synthesizer = get_response_synthesizer(llm=llm, response_mode=ResponseMode.COMPACT)

    # 1. INPUT validation (guard) — empty query never reaches the network. No LLM here.
    @step
    async def validate_input(self, ctx: Context, ev: QueryStartEvent) -> CleanQueryEvent | StopEvent:
        clean = " ".join((ev.user_query or "").split())   # trim + collapse whitespace/newlines
        if not clean:
            return StopEvent(result={"answer": "❓ Please enter a question.", "nodes": []})
        # user_query is needed by several later steps → it lives in STATE, set once.
        await ctx.store.set("user_query", clean)
        return CleanQueryEvent(user_query=clean)

    # 2. Retrieve — OUTPUT validation lives next to the step that produced it.
    @step
    async def retrieve(self, ctx: Context, ev: CleanQueryEvent) -> RetrievedEvent | NoResultsEvent:
        candidates = await self.retriever.aretrieve(ev.user_query)
        if not candidates:
            return NoResultsEvent(error_message="No relevant information found in the documents.")
        return RetrievedEvent(candidates=candidates)

    # 3. Rerank — pure reordering; it trusts it received non-empty candidates.
    @step
    async def rerank(self, ctx: Context, ev: RetrievedEvent) -> RerankedEvent:
        user_query = await ctx.store.get("user_query")
        nodes = self.reranker.postprocess_nodes(ev.candidates, query_str=user_query)
        return RerankedEvent(nodes=nodes)

    # 4. Confidence check (router) — strong enough? answer. Too weak? retry.
    @step
    async def check_confidence(self, ctx: Context, ev: RerankedEvent) -> SynthesizeEvent | RetryEvent:
        top_score = ev.nodes[0].score if ev.nodes else 0.0
        if top_score < CONFIDENCE_THRESHOLD:
            return RetryEvent(reason="low_confidence")
        return SynthesizeEvent(nodes=ev.nodes)

    # 5. Retry from a wider angle (router + STATE) — bounded by MAX_RETRIES.
    @step
    async def retry_search(self, ctx: Context, ev: RetryEvent) -> RetrievedEvent | NoResultsEvent:
        attempts = await ctx.store.get("attempts", default=0)   # counter survives the loop → STATE
        if attempts >= MAX_RETRIES:
            return NoResultsEvent(error_message="Couldn't find a confident enough answer to your question.")
        await ctx.store.set("attempts", attempts + 1)

        user_query = await ctx.store.get("user_query")
        # "Different angle" here = cast a wider net each round.
        wider = self.index.as_retriever(similarity_top_k=self.candidate_k * (attempts + 2))
        candidates = await wider.aretrieve(user_query)
        if not candidates:
            return NoResultsEvent(error_message="No relevant information found in the documents.")
        return RetrievedEvent(candidates=candidates)   # re-enters rerank → check_confidence (the loop)

    # 6. Synthesize — the only step that calls the LLM.
    @step
    async def synthesize(self, ctx: Context, ev: SynthesizeEvent) -> StopEvent:
        user_query = await ctx.store.get("user_query")
        response = await self.synthesizer.asynthesize(user_query, ev.nodes)
        return StopEvent(result={"answer": response.response, "nodes": response.source_nodes})

    # 7. Terminal handler for every "nothing useful" path.
    @step
    async def handle_no_results(self, ctx: Context, ev: NoResultsEvent) -> StopEvent:
        return StopEvent(result={"answer": f"🔍 {ev.error_message}", "nodes": []})


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
        # Every StopEvent now returns the SAME shape: {"answer": str, "nodes": list}.
        result = await workflow.run(user_query=message)
        answer, nodes = result["answer"], result["nodes"]
        if not nodes:
            return answer
        return (
            f"{answer}\n\n"
            f"---\n\n"
            f"<details><summary>📄 Sources</summary>\n\n"
            f"{format_sources(nodes)}\n\n</details>"
        )
    return chat


if __name__ == "__main__":
    workflow = RAGWorkflow(timeout=60)
    build_app(make_chat(workflow)).launch()
