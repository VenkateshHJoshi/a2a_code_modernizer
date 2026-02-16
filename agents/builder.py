from agents.base_agent import BaseAgent

class BuilderAgent(BaseAgent):
    def get_task_prompt(self, payload: dict) -> str:
        legacy_code = payload.get("legacy_code", "")
        plan = payload.get("plan", "")
        
        return (
            f"Refactor the legacy code based on the Architect's plan.\n\n"
            f"Plan: {plan}\n\n"
            "Requirements:\n"
            "1. Use modern Python 3.10+ syntax.\n"
            "2. Add Type Hints.\n"
            "3. Ensure PEP8 compliance.\n"
            "4. Return ONLY the valid JSON response with the new code.\n"
            "JSON Format: { 'success': true, 'data': { 'code': 'the complete refactored python code string' } }.\n\n"
            f"Legacy Code:\n{legacy_code}"
        )