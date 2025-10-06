from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..db.db import get_chunk_by_id 

router = APIRouter(
    prefix="/api/v1/chunk",
    tags=["Chunk Retrieval"],
    responses={404: {"description": "Chunk not found"}},
)

@router.get("/{chunk_id}", response_model=Dict[str, Any])
async def retrieve_chunk(chunk_id: str) -> Dict[str, Any]:
    """
    Retrieve a single code chunk by its unique chunkId.
    """
    chunk = await get_chunk_by_id(chunk_id)
    
    if chunk is None:
        raise HTTPException(status_code=404, detail=f"Chunk with ID '{chunk_id}' not found")
        
    return chunk