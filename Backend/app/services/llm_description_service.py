import os
from google import genai
from google.genai.errors import APIError

# --- Initialization ---
try:
    client = genai.Client()
except Exception as e:
    # Handle case where API key might not be available at import time
    print(f"Warning: Gemini client initialization failed. API calls will fail unless GEMINI_API_KEY is set. Error: {e}")
    client = None

# --- Prompt Definition ---
SYSTEM_PROMPT = (
    "You are an expert AI assistant tasked with summarizing code chunks. "
    "The code is written in **MeTTa**, a language for symbolic AI used in the OpenCog Hyperon project. "
    "Your output MUST be a concise, human-readable description (max 2-3 sentences) of the chunk's core function, rule, or intent. "
    "DO NOT include any MeTTa code syntax, file paths, or variable names from the code. "
    "Focus only on what the code *does* conceptually."
)

MODEL_NAME = "gemini-2.5-flash"


async def generate_description(code_chunk: str) -> str | None:
    """
    Sends a MeTTa code chunk to the Gemini API to generate a human-readable description.

    Args:
        code_chunk: The raw MeTTa code string to summarize.

    Returns:
        The generated description string, or None if the API call fails.
    """
    if not client:
        return f"Error: Gemini client is not initialized. Code chunk too long: {len(code_chunk)} chars."
    
    try:
        # We use client.models.generate_content for a simple, quick text generation.
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                {"role": "user", "parts": [{"text": code_chunk}]}
            ],
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.0  
            )
        )
        
        # Strip whitespace and return the description
        return response.text.strip()
    
    except APIError as e:
        print(f"Gemini API Error for chunk: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during API call: {e}")
        return None

# for test (but not executed directly in the backend)
# if __name__ == '__main__':
#     import asyncio
#     sample_metta_code = "(define (factorial n) (if (= n 0) 1 (* n (factorial (- n 1)))))"
#     description = asyncio.run(generate_description(sample_metta_code))
#     print(f"MeTTa Code: {sample_metta_code}")
#     print(f"Description: {description}")