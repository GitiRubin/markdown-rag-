# Environment
from netfree_unstrict_ssl import unstrict_ssl
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import StorageContext, VectorStoreIndex

unstrict_ssl()
load_dotenv()

# Loading
from llama_index.core import SimpleDirectoryReader

reader = SimpleDirectoryReader(input_dir=r"md_files")
documents = reader.load_data()

# Chunking
# Split along the markdown structure (one node per section), then use a
# SentenceSplitter as a safety net to cap any oversized section.

from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter

md_parser = MarkdownNodeParser()
md_nodes = md_parser.get_nodes_from_documents(documents=documents, show_progress=True)

splitter = SentenceSplitter(chunk_size=256, chunk_overlap=40)
nodes = splitter.get_nodes_from_documents(documents=md_nodes, show_progress=True)

# Embedding

COHERE_API_KEY = os.environ["COHERE_API_KEY"]
from llama_index.embeddings.cohere import CohereEmbedding

# with input_typ='search_document'
embed_model = CohereEmbedding(
    api_key=COHERE_API_KEY,
    model_name="embed-english-v3.0",
    input_type="search_document",
)

# Indexing and Saving

PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
NAMESPACE = os.environ["NAMESPACE"]

pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index("rag")
pincone_vector_store= PineconeVectorStore(pinecone_index=pinecone_index, namespace=NAMESPACE)

storage_context = StorageContext.from_defaults(vector_store=pincone_vector_store)

index = VectorStoreIndex.from_documents(
    nodes, storage_context=storage_context, embed_model=embed_model
)

