import os
import hashlib
import json
import shutil
from loguru import logger
from typing import Optional, List, Dict, Any, Union 

def hash_file_content(filepath: str) -> str:
    """Calculates the SHA256 hash of a file's content."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash file {filepath}: {e}")
        return "" # Return empty hash on failure

def get_file_content(filepath: str) -> str:
    """
    Helper to read and return file content, implementing robust encoding 
    and error logging.
    """
    try:
        # 1. Try reading with standard UTF-8 encoding
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        return content
            
    except UnicodeDecodeError as e:
        logger.warning(f"Failed to read {filepath} with UTF-8 due to UNICODE error. Trying 'latin-1'. Error: {e}")
        # 2. Fallback to 'latin-1' (handles many non-standard encodings)
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as fallback_e:
            logger.error(f"Fallback read failed for {filepath}: {fallback_e}")
            return ""
            
    except Exception as e:
        logger.error(f"Failed to read file {filepath} (non-encoding error): {e}")
        return ""

def process_metta_files(
    file_paths: List[str],
    output_dir: str,
    repo_root: Optional[str] = None,
    json_path: str = "../metta_index.json"
) -> List[Dict[str, Any]]:
    """
    Processes Metta files, filters out empty content, and returns a list 
    of chunk dictionaries for DB insertion.
    """
    os.makedirs(output_dir, exist_ok=True)
    index: Dict[str, str] = {}
    db_chunks: List[Dict[str, Any]] = []

    repo_name: str = os.path.basename(os.path.normpath(repo_root)) if repo_root else "repo"
    
    # Define required metadata placeholders
    PROJECT_NAME = "MeTTa-AI-Assistant"
    VERSION_TAG = "main"

    for file in file_paths:
        if file.endswith(".metta"):
            
            content: str = get_file_content(file)
            
            stripped_content = content.strip()
            
            if not stripped_content:
                logger.warning(f"Skipping file {file} (Path: {file}): Content is empty or only whitespace. Not processing.")
                continue
        
            
            # The hash must be calculated after content check
            file_hash: str = hash_file_content(file)
            new_name: str = f"{file_hash}.metta"

            rel_path_inside_repo: str = (
                os.path.relpath(file, repo_root).replace("\\", "/") if repo_root else os.path.basename(file)
            )
            
            # Build the complete chunk dictionary
            db_chunks.append({
                "chunkId": file_hash,
                "content": content,
                "filePath": f"{repo_name}/{rel_path_inside_repo}", 
                "annotation": None,
                
                # Fields required by Pydantic schema validation:
                "source": "code", # Literal value for Metta code
                "chunk": content,         
                "project": PROJECT_NAME,
                "repo": repo_name,
                "section": "full_file",
                "file": rel_path_inside_repo,
                "version": VERSION_TAG,
            })
            
            # Update the file index 
            index[file_hash] = f"{repo_name}/{rel_path_inside_repo}"

            # Copy the file to the output directory (local cache)
            dest_path: str = os.path.join(output_dir, new_name)
            shutil.copy(file, dest_path)

            logger.info(f"Processed {rel_path_inside_repo} → {new_name}")

    # The cleanup section remains as a pass
    if repo_root and os.path.exists(repo_root):
        pass

    # Save the index to disk
    json_full_path: str = os.path.join(output_dir, json_path)
    with open(json_full_path, "w") as f:
        json.dump(index, f, indent=2)

    logger.info(f"Index saved at {json_full_path}")
    
    # Return the chunks list for DB insertion
    return db_chunks
