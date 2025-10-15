import time
import logging
from tqdm import tqdm
from langchain_community.vectorstores import Milvus
from langchain_openai import AzureOpenAIEmbeddings
from pymilvus import utility, connections, MilvusException
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def connect_to_milvus(retries=5, delay=10):
    """Establishes a connection to Milvus with a retry mechanism."""
    for i in range(retries):
        try:
            # Check if a connection with the alias 'default' already exists
            if 'default' in connections.list_connections():
                connections.disconnect('default')
            
            connections.connect("default", host=config.MILVUS_HOST, port=config.MILVUS_PORT)
            logger.info("Successfully connected to Milvus.") # Changed to logger
            return True
        except MilvusException as e:
            logger.warning(f"Failed to connect to Milvus (Attempt {i+1}/{retries}): {e}")
            if i < retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error("Could not connect to Milvus after multiple attempts.")
                return False

def get_milvus_retrievers():
    """Initializes connection to Milvus and returns LangChain retrievers."""
    logger.info("Initializing Milvus Vector Store...")
    
    if not connect_to_milvus(): # Ensure connection is active
        return None, None

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=config.AZURE_EMBEDDING_DEPLOYMENT_NAME,
        api_key=config.AZURE_API_KEY,
        azure_endpoint=config.AZURE_API_BASE,
        api_version=config.AZURE_API_VERSION
    )

    try:
        if not utility.has_collection(config.QURAN_COLLECTION) or not utility.has_collection(config.HADITH_COLLECTION):
            logger.error("Collections not found in Milvus. Please run the '/ingest' endpoint first.")
            return None, None
        
        quran_vector_store = Milvus(embeddings, collection_name=config.QURAN_COLLECTION, connection_args={"host": config.MILVUS_HOST, "port": config.MILVUS_PORT})
        hadith_vector_store = Milvus(embeddings, collection_name=config.HADITH_COLLECTION, connection_args={"host": config.MILVUS_HOST, "port": config.MILVUS_PORT})
        
        logger.info("Milvus Retrievers Initialized Successfully.")
        return quran_vector_store.as_retriever(search_kwargs={"k": 5}), hadith_vector_store.as_retriever(search_kwargs={"k": 5})
    except Exception as e:
        logger.error(f"Error initializing retrievers: {e}")
        return None, None

def ingest_data_to_milvus(collection_name, documents):
    """Ingests chunked documents into a Milvus collection in batches."""
    logger.info(f"Starting data ingestion for '{collection_name}'")
    
    if not connect_to_milvus():
        raise ConnectionError("Could not connect to Milvus for ingestion.")

    if utility.has_collection(collection_name):
        logger.info(f"Collection '{collection_name}' already exists. Dropping for fresh ingestion.")
        utility.drop_collection(collection_name)
    
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=config.AZURE_EMBEDDING_DEPLOYMENT_NAME,
        api_key=config.AZURE_API_KEY,
        azure_endpoint=config.AZURE_API_BASE,
        api_version=config.AZURE_API_VERSION
    )
    
    batch_size = 500
    vector_store = None

    logger.info(f"Ingesting {len(documents)} documents in batches of {batch_size}...")
    for i in tqdm(range(0, len(documents), batch_size)):
        batch = documents[i:i + batch_size]
        if vector_store is None:
            vector_store = Milvus.from_documents(batch, embeddings, collection_name=collection_name, connection_args={"host": config.MILVUS_HOST, "port": config.MILVUS_PORT})
        else:
            vector_store.add_documents(batch)
        
        logger.info(f"Batch {i//batch_size + 1} ingested. Pausing for 20 seconds to respect API limits...")
        time.sleep(20)
    
    logger.info(f"Data ingestion for '{collection_name}' complete.")