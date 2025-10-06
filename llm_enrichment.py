import os
from pymongo import MongoClient
from loguru import logger
from google import genai
from google.genai.errors import APIError
from typing import Dict, Any, List

# --- Configuration ---
# NOTE: Replace with your actual connection details
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "chunkDB"
COLLECTION_NAME = "chunks"

# --- LLM Client Setup ---
# The client automatically picks up the GEMINI_API_KEY environment variable
try:
    llm_client = genai.Client()
    LLM_MODEL = "gemini-2.5-flash" # Fast, capable model for summarization
except Exception as e:
    logger.error(f"Failed to initialize Gemini Client: {e}")
    llm_client = None

# --- Core Functions ---

def generate_summary(content: str) -> str:
    """Sends the chunk content to Gemini for a concise summary."""
    if not llm_client:
        return "LLM_SERVICE_DOWN"
        
    prompt = (
        "Analyze the following Metta code (Open-NARS style logic programming). "
        "Provide a single, concise sentence summarizing the purpose and function of the code block. "
        "DO NOT use quotes, special formatting, or specific file names in the summary. Code:\n\n"
        f"--- CODE ---\n{content}\n--- END CODE ---"
    )
    
    try:
        response = llm_client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt
        )
        # Clean up the response (strip whitespace, ensure it's a single line)
        summary = response.text.strip().replace('\n', ' ')
        return summary
    except APIError as e:
        logger.error(f"Gemini API Error for content: {content[:30]}... Error: {e}")
        return "LLM_API_ERROR"
    except Exception as e:
        logger.error(f"Unexpected error during summary generation: {e}")
        return "GENERATION_FAILED"


def enrich_chunks_with_summary() -> None:
    """
    Connects to MongoDB, finds chunks lacking a summary, generates summaries,
    and updates the documents.
    """
    try:
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client[DATABASE_NAME]
        chunks_collection = db[COLLECTION_NAME]
        logger.info(f"Connected to MongoDB: {MONGO_URI}, Collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return

    # Find chunks that have been processed but lack a summary field
    # We filter by 'project' to only target the metta chunks
    query = {
        "project": "MeTTa-AI-experiment", 
        "$or": [
            {"summary": {"$exists": False}}, 
            {"summary": None}
        ]
    }
    
    chunks_to_process: List[Dict[str, Any]] = list(chunks_collection.find(query))
    total_count = len(chunks_to_process)
    logger.info(f"Found {total_count} chunks needing summarization.")

    if total_count == 0:
        logger.info("No new chunks require LLM summarization. Exiting.")
        return

    # Process chunks one by one
    for i, chunk in enumerate(chunks_to_process):
        chunk_id = chunk.get("chunkId", "UNKNOWN_ID")
        content = chunk.get("content", "")
        
        if not content:
            logger.warning(f"Skipping chunk {chunk_id}: Content is empty.")
            continue
            
        logger.info(f"[{i+1}/{total_count}] Generating summary for {chunk_id[:8]}...")
        summary = generate_summary(content)

        if summary not in ("LLM_API_ERROR", "LLM_SERVICE_DOWN", "GENERATION_FAILED"):
            # Update the document in the database
            chunks_collection.update_one(
                {"_id": chunk["_id"]},
                {"$set": {"summary": summary}}
            )
            logger.success(f"Successfully added summary to {chunk_id[:8]}")
        else:
            logger.error(f"Failed to summarize {chunk_id[:8]}. Status: {summary}")

    logger.info("LLM enrichment process completed.")
    mongo_client.close()


if __name__ == "__main__":
    enrich_chunks_with_summary()