from netfree_unstrict_ssl import unstrict_ssl
unstrict_ssl()                      # must run before any HTTPS client is built

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.llms.openai import OpenAI

load_dotenv()

# secrets
COHERE_API_KEY = os.environ["COHERE_API_KEY"]
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# constants
INDEX_NAME = "rag"
EMBED_MODEL = "embed-english-v3.0"
NAMESPACE = "resume_formatter"
LLM_MODEL = "gpt-4o"
STRUCTURED_DATA_PATH = "structured_data.json"   # output of the Data Extraction stage

# shared clients — created once, imported everywhere
pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index(INDEX_NAME)
pincone_vector_store= PineconeVectorStore(pinecone_index=pinecone_index, namespace=NAMESPACE)
llm = OpenAI(api_key=OPENAI_API_KEY, model=LLM_MODEL)
