from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import PayloadSchemaType
from loguru import logger
async def setup_metadata_indexes(qdrant_client: AsyncQdrantClient, collection_name: str):
    metadata_fields = {
        "chunkId": PayloadSchemaType.KEYWORD,
        "project": PayloadSchemaType.KEYWORD,
        "repo": PayloadSchemaType.KEYWORD,
        "file": PayloadSchemaType.KEYWORD,
        "section": PayloadSchemaType.KEYWORD,
        "version": PayloadSchemaType.KEYWORD,
        "source": PayloadSchemaType.KEYWORD,
    }

    for field, schema in metadata_fields.items():
        try:
            await qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name=field,
                field_schema=schema,
            )
            logger.info(f"Metadata index created for '{field}'")
        except Exception as e:
            if "already exists" in str(e):
                logger.warning(f"Index for '{field}' already exists")
            else:
                logger.error(f"Failed to create index for '{field}': {e}")
