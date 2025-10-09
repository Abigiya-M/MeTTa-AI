import asyncio
from typing import List, Dict, Any
from ..db import db as db_operations
from Backend.app.services.llm_description_service import generate_description

async def annotate_chunks(limit: int = 100) -> Dict[str, Any]:
    """
    Fetches un-annotated code chunks, generates descriptions using LLM, 
    and updates the database.

    Args:
        limit: The maximum number of chunks to process in one run.

    Returns:
        A dictionary summarizing the annotation results.
    """
    
    # 1. Fetch chunks that need annotation (where 'description' is null)
    filter_query = {"description": {"$exists": False}, "source": "code"}
    
    print(f"Fetching up to {limit} un-annotated code chunks...")
    
    # Use the existing get_chunks function from your db module
    chunks_to_process = await db_operations.get_chunks(filter_query=filter_query, limit=limit)
    
    if not chunks_to_process:
        return {"status": "success", "message": "No un-annotated chunks found to process."}

    print(f"Found {len(chunks_to_process)} chunks for annotation.")

    # 2. Process chunks asynchronously
    
    # Create a list of tasks for generating descriptions and updating the database
    annotation_tasks = []
    
    for chunk in chunks_to_process:
        chunk_id = chunk.get("chunkId")
        raw_code = chunk.get("chunk")
        
        # Use asyncio.create_task to run the generation and update concurrently
        task = asyncio.create_task(_process_single_chunk(chunk_id, raw_code))
        annotation_tasks.append(task)

    # Wait for all tasks to complete
    results = await asyncio.gather(*annotation_tasks)

    # 3. Compile results
    
    successful_annotations = sum(1 for status in results if status == True)
    failed_annotations = len(results) - successful_annotations
    
    return {
        "status": "completed",
        "processed_count": len(chunks_to_process),
        "successful_annotations": successful_annotations,
        "failed_annotations": failed_annotations,
        "message": f"Finished annotating {successful_annotations} chunks."
    }

async def _process_single_chunk(chunk_id: str, raw_code: str) -> bool:
    """Helper function to generate description and update the DB for one chunk."""
    
    print(f"-> Processing chunk: {chunk_id}")
    
    # Generate the description using the LLM service
    description = await generate_description(raw_code)
    
    if description:
        # Update the database with the new description
        updates = {"annotation": description}
        modified_count = await db_operations.update_chunk(chunk_id, updates)
        
        if modified_count == 1:
            print(f"<- Successfully annotated chunk: {chunk_id}")
            return True
        else:
            print(f"<- Failed to update DB for chunk: {chunk_id} (No doc modified)")
            return False
    else:
        print(f"<- Failed to generate description for chunk: {chunk_id}")
        return False

# to run and test
# if __name__ == '__main__':
#     result = asyncio.run(annotate_chunks(limit=5))
#     print(result)
