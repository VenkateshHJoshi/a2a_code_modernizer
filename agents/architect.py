from agents.base_agent import BaseAgent

class ArchitectAgent(BaseAgent):
    def get_task_prompt(self, payload: dict) -> str:
        code = payload.get("legacy_code", "")
        return (
            "Analyze the following legacy Python code. "
            "Identify issues (e.g., lack of type hinting, old syntax, poor structure). "
            "Propose a modernization plan. "
            "Respond with JSON containing { 'success': true, 'data': { 'plan': 'string description of changes' } }.\n\n"
            f"Code:\n{code}"
        )