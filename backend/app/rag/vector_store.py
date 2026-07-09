import os
import logging
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config Env
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers").lower()
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

def get_embeddings():
    """
    Instantiates embeddings model based on environment variable provider.
    """
    if EMBEDDING_PROVIDER == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in env. Falling back to local SentenceTransformers.")
            return HuggingFaceEmbeddings(model_name=os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2"))
        return OpenAIEmbeddings(
            openai_api_key=api_key,
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )
    else:
        # Default local HuggingFace embeddings
        model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
        logger.info(f"Using HuggingFace local embeddings: {model_name}")
        return HuggingFaceEmbeddings(model_name=model_name)

def get_vector_store() -> Chroma:
    """
    Connects to or instantiates the Chroma vector database.
    """
    embeddings = get_embeddings()
    # Create DB dir if it doesn't exist
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings,
        collection_name="whmcs_modules_kb"
    )

def chunk_scraped_item(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Chunks a single crawled product/article into smaller chunks with meta attributes.
    """
    chunks_with_metadata = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    url = item.get("url", "")
    title = item.get("title", "")
    item_type = item.get("type", "document")

    if item_type == "product":
        # Formulate a structured product description for RAG search
        content = (
            f"Product Module Name: {title}\n"
            f"Price: {item.get('price_text', 'Contact for Price')}\n"
            f"Category: {', '.join(item.get('categories', []))}\n"
            f"Short Summary: {item.get('short_description', '')}\n"
            f"Key Features: {', '.join(item.get('features', []))}\n"
            f"Compatibility: {', '.join(item.get('compatibility', []))}\n"
            f"Full Features & Setup Details:\n{item.get('full_description', '')}"
        )
        
        # Add FAQs to product chunks if they exist
        faqs = item.get("faqs", [])
        for faq in faqs:
            content += f"\nFAQ: Q: {faq.get('question')} A: {faq.get('answer')}"

        # Split product content
        docs = text_splitter.create_documents(
            texts=[content],
            metadatas=[{
                "url": url,
                "title": title,
                "type": "product",
                "price": item.get("price_numeric", 0.0),
                "categories": ",".join(item.get("categories", []))
            }]
        )
        for doc in docs:
            chunks_with_metadata.append({
                "text": doc.page_content,
                "metadata": doc.metadata
            })
    else:
        # standard guide/blog document
        content = (
            f"Article Title: {title}\n"
            f"Categories: {', '.join(item.get('categories', []))}\n"
            f"Content:\n{item.get('content', '')}"
        )
        
        docs = text_splitter.create_documents(
            texts=[content],
            metadatas=[{
                "url": url,
                "title": title,
                "type": "document",
                "categories": ",".join(item.get("categories", []))
            }]
        )
        for doc in docs:
            chunks_with_metadata.append({
                "text": doc.page_content,
                "metadata": doc.metadata
            })

    return chunks_with_metadata

def update_vector_db_with_scraped_data(scraped_data: List[Dict[str, Any]]):
    """
    Clears existing collection and updates it with newly crawled content chunks.
    """
    logger.info("Initializing vector DB updates...")
    db = get_vector_store()
    
    # Simple clean reset of collection
    try:
        db.delete_collection()
        # Re-initialize
        db = get_vector_store()
    except Exception as e:
        logger.warning(f"Error resetting database collection: {e}")

    all_texts = []
    all_metadatas = []
    
    for item in scraped_data:
        chunks = chunk_scraped_item(item)
        for chunk in chunks:
            all_texts.append(chunk["text"])
            all_metadatas.append(chunk["metadata"])

    if all_texts:
        logger.info(f"Adding {len(all_texts)} text chunks to Chroma vector database...")
        # Chroma handles indexing under the hood
        db.add_texts(texts=all_texts, metadatas=all_metadatas)
        logger.info("Chroma indexing complete.")
    else:
        logger.warning("No crawled text chunks found to store.")

def query_vector_db(query: str, n_results: int = 4) -> List[Dict[str, Any]]:
    """
    Queries Chroma vector store to find semantically relevant knowledge chunks.
    """
    db = get_vector_store()
    try:
        results = db.similarity_search_with_relevance_scores(query, k=n_results)
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": score
            })
        return formatted_results
    except Exception as e:
        logger.error(f"Error querying Chroma vector database: {e}")
        return []
