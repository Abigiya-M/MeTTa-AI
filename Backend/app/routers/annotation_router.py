from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from ..services.chunk_annotation_service import annotate_chunks # Go up to 'app' then down to 'services'

router = APIRouter(
    prefix="/annotation",
    tags=["Chunk Annotation"],
    responses={404: {"description": "Not found"}},
)

@router.post("/process-chunks", response_model=Dict[str, Any])
async def trigger_chunk_annotation(
    limit: int = Query(
        100, 
        gt=0, 
        description="Maximum number of un-annotated chunks to process in this run."
    )
) -> Dict[str, Any]:
    """
    Triggers the background task to find un-annotated chunks, generate 
    descriptions using the Gemini LLM, and store them in the database.
    """
    try:
        results = await annotate_chunks(limit=limit)
        return results
    except Exception as e:
        print(f"Error during chunk annotation process: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An internal error occurred during annotation: {e}"
        )