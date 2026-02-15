import ollama
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.client = ollama.Client(host='http://localhost:11434')

    def check_ollama_status(self) -> bool:
        """Checks if Ollama is running."""
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama not reachable: {e}")
            return False

    def get_local_models(self) -> List[str]:
        """Returns a list of locally available model names."""
        try:
            models = self.client.list()
            return [m['name'] for m in models.get('models', [])]
        except Exception:
            return []

    def find_compatible_coding_model(self) -> Optional[str]:
        """
        Scans local models for coding-specific keywords.
        Returns the model name if found, else None.
        """
        local_models = self.get_local_models()
        coding_keywords = ['code', 'codellama', 'deepseek-coder', 'wizardcoder']
        
        for model in local_models:
            for keyword in coding_keywords:
                if keyword in model.lower():
                    return model
        return None

    def pull_model(self, model_name: str, status_callback=None):
        """
        Pulls a model from Ollama library.
        status_callback: Optional function to update UI (e.g., streamlit.write)
        """
        try:
            if status_callback:
                status_callback(f"Initiating download for {model_name}... This may take a moment.")
            
            # Stream the download progress
            for progress in self.client.pull(model_name, stream=True):
                if status_callback and 'total' in progress and 'completed' in progress:
                    total = progress['total']
                    completed = progress['completed']
                    percent = (completed / total) * 100
                    status_callback(f"Downloading {model_name}: {percent:.1f}%")
            
            if status_callback:
                status_callback(f"Successfully downloaded {model_name}.")
            return True
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            if status_callback:
                status_callback(f"Error downloading model: {e}")
            return False

model_manager = ModelManager()