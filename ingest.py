# Environment
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from config import pincone_vector_store, COHERE_API_KEY, EMBED_MODEL

# Loading
reader = SimpleDirectoryReader(input_dir=r"md_files")
documents = reader.load_data()

# Chunking
# Split along the markdown structure (one node per section), then use a
# SentenceSplitter as a safety net to cap any oversized section.
md_parser = MarkdownNodeParser()
md_nodes = md_parser.get_nodes_from_documents(documents=documents, show_progress=True)

splitter = SentenceSplitter(chunk_size=256, chunk_overlap=40)
nodes = splitter.get_nodes_from_documents(documents=md_nodes, show_progress=True)


# with input_type='search_document'
embed_model = CohereEmbedding(
    api_key=COHERE_API_KEY,
    model_name=EMBED_MODEL,
    input_type="search_document",
)

# Indexing and Saving


storage_context = StorageContext.from_defaults(vector_store=pincone_vector_store)

index = VectorStoreIndex.from_documents(
    nodes, storage_context=storage_context, embed_model=embed_model
)

