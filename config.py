import os
from dotenv import load_dotenv

load_dotenv()

# Priority Selection: Defaults to 'groq' so it goes first.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower().strip()

# Azure Credentials
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
_base_url = os.getenv("AZURE_API_BASE", "").strip()
if _base_url and not _base_url.endswith("/"):
    _base_url += "/"
AZURE_API_BASE = _base_url

AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2024-08-01-preview")
AZURE_EMBEDDING_DEPLOYMENT_NAME = os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME")
AZURE_CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_CHAT_DEPLOYMENT_NAME")

# Groq Credentials
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

# Search Tool Configuration
SEARXNG_ENDPOINT = os.getenv("SEARXNG_ENDPOINT")
WIKIPEDIA_LANG = os.getenv("WIKIPEDIA_LANG", "en")
SEARXNG_ENGINES = os.getenv("SEARXNG_ENGINES", "google,bing,duckduckgo,wikipedia")

# Milvus Configuration
MILVUS_HOST = os.getenv("MILVUS_HOST", "milvus-standalone")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
QURAN_COLLECTION = os.getenv("MILVUS_QURAN_COLLECTION")
HADITH_COLLECTION = os.getenv("MILVUS_HADITH_COLLECTION")