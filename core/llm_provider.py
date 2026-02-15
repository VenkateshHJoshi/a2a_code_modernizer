import google.generativeai as genai
from typing import Optional
from config import settings
import ollama
import logging

logger = logging.getLogger(__name__)

class HybridLLM:
    def __init__(self):
        # Configure Gemini if key exists
        self.gemini_available = False
        if settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(settings.fallback_model)
                self.gemini_available = True
            except Exception as e:
                logger.error(f"Gemini setup failed: {e}")
        
        self.ollama_client = ollama.Client(host=settings.ollama_host)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Tries to generate text using Local Ollama.
        Falls back to Google Gemini if Ollama fails.
        """
        # 1. Attempt Local Inference (Ollama)
        try:
            logger.info(f"Attempting Ollama inference with {settings.preferred_local_model}...")
            response = self.ollama_client.chat(
                model=settings.preferred_local_model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response['message']['content']
        
        except Exception as e:
            logger.warning(f"Ollama inference failed: {e}. Attempting fallback...")
            
            # 2. Fallback to Cloud (Gemini)
            if not self.gemini_available:
                raise RuntimeError("Both Ollama and Gemini are unavailable. Please check your setup.")
            
            try:
                logger.info(f"Using Gemini fallback ({settings.fallback_model})...")
                # Construct the prompt for Gemini (Gemini API handles system prompts slightly differently depending on version, 
                # here we prepend for safety or use specific instruction field)
                full_prompt = f"{system_prompt}\n\nUser Request:\n{prompt}"
                
                response = self.gemini_model.generate_content(full_prompt)
                return response.text
            except Exception as gemini_error:
                logger.error(f"Gemini inference failed: {gemini_error}")
                raise RuntimeError("All inference methods failed.")

llm_provider = HybridLLM()