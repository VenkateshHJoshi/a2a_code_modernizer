import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- Model Configuration ---
    LOCAL_MODEL_NAME = "qwen2.5-coder:3b"
    # Updated to the model you requested
    FALLBACK_MODEL_NAME = "gemini-3-flash-preview"
    
    # --- API Keys ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # --- Agent System Settings ---
    MAX_RETRIES = 3
    TEMPERATURE = 0.2 
    
    # --- System Prompts ---
    
    ARCHITECT_SYSTEM_PROMPT = (
        "You are a Senior Software Architect. Analyze the legacy code. "
        "You MUST respond with a valid JSON object. "
        "CRITICAL: Use DOUBLE QUOTES (\") for all keys and string values. Do NOT use single quotes. "
        "Format: { 'success': true, 'data': { 'plan': 'Your detailed text plan here' } }"
    )
    
    BUILDER_SYSTEM_PROMPT = (
        "You are an Expert Python Developer. Refactor the code. "
        "CRITICAL: Use DOUBLE QUOTES (\") for all keys and strings in your JSON response. "
        "The JSON must have 'success': true, and 'data': { 'code': '...' }. "
        "REQUIREMENT: The code MUST end with a `if __name__ == '__main__':` block that calls the functions and prints the results, so the user can see it running. "
        "Format: { 'success': true, 'data': { 'code': 'def func(): ...\\nif __name__...': } }"
    )
    
    QA_SYSTEM_PROMPT = (
        "You are a QA Engineer. Review the code. "
        "CRITICAL: Use DOUBLE QUOTES (\") for all keys and strings in your JSON response. "
        "You MUST include a 'test_cases' list with at least 3 items. Each item must have 'name' and 'code'. "
        "Format: { 'success': true, 'data': { 'review': '...', 'test_cases': [ {'name': 'Test 1', 'code': '...'}, ... ] } }"
    )
    
    LIBRARIAN_SYSTEM_PROMPT = (
        "You are a Technical Writer. Generate markdown documentation. "
        "CRITICAL: Use DOUBLE QUOTES (\") for all keys and strings in your JSON response. "
        "Format: { 'success': true, 'data': { 'documentation': '# Title\\nContent' } }"
    )