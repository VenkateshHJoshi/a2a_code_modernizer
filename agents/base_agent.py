import json
import re
import ast # Import ast for fallback parsing
from abc import ABC, abstractmethod
from core.llm_provider import HybridLLMProvider
from core.protocol import TaskResult

class BaseAgent(ABC):
    def __init__(self, llm_provider: HybridLLMProvider, name: str, system_prompt: str):
        self.llm_provider = llm_provider
        self.name = name
        self.system_prompt = system_prompt

    @abstractmethod
    def get_task_prompt(self, payload: dict) -> str:
        """Constructs the specific prompt for this agent based on the payload."""
        pass

    def execute(self, payload: dict, retry_context: str = None) -> TaskResult:
        # 1. Build Prompt
        user_prompt = self.get_task_prompt(payload)
        full_system_prompt = (
            f"{self.system_prompt}\n"
            "CRITICAL RULE: You must respond ONLY with a valid JSON object. "
            "Use DOUBLE QUOTES (\"), not single quotes. "
            "Do not include markdown code blocks (```json ... ```). Just the raw JSON text. "
            "Ensure the JSON keys are exactly 'success', 'data', and optionally 'error_message'."
        )
        
        if retry_context:
            user_prompt = f"{user_prompt}\n\n[RETRY CONTEXT - FIX THESE ERRORS]\n{retry_context}\nPlease fix the issues mentioned above and output valid JSON."

        # 2. Call LLM
        try:
            raw_response = self.llm_provider.generate(user_prompt, full_system_prompt)
        except Exception as e:
            return TaskResult(success=False, error_message=f"LLM Connection failed: {str(e)}", sender=self.name)

        # DEBUG: Print raw response to terminal
        print(f"[{self.name}] RAW RESPONSE:\n{raw_response[:500]}...") 

        # 3. Parse Response
        clean_response = raw_response.strip()
        if "```json" in clean_response:
            clean_response = clean_response.split("```json")[1].split("```")[0]
        elif "```" in clean_response:
            clean_response = clean_response.split("```")[1].split("```")[0]
            
        try:
            # Primary: Try standard JSON parsing
            data_dict = json.loads(clean_response)
        except json.JSONDecodeError:
            # Fallback: Try AST Literal Eval (handles Python dict style with single quotes)
            try:
                print(f"[{self.name}] JSON failed, trying AST fallback...")
                data_dict = ast.literal_eval(clean_response)
            except Exception as e:
                print(f"[{self.name}] Parsing failed completely: {e}")
                return TaskResult(
                    success=False,
                    error_message=f"Invalid JSON/Dict returned. Error: {str(e)}",
                    data={"raw_response": raw_response},
                    sender=self.name
                )
            
        # Basic Validation
        is_successful = data_dict.get("success", True)
        
        return TaskResult(
            success=is_successful,
            data=data_dict.get("data", {}),
            error_message=data_dict.get("error_message"),
            syntax_errors=data_dict.get("syntax_errors", []),
            sender=self.name
        )