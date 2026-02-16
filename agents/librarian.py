from agents.base_agent import BaseAgent

class LibrarianAgent(BaseAgent):
    def get_task_prompt(self, payload: dict) -> str:
        code = payload.get("code", "")
        return (
            "Generate comprehensive documentation for the code. "
            "Include a docstring for the class/functions and a usage example. "
            "JSON Format: { 'success': true, 'data': { 'documentation': 'markdown string' } }.\n\n"
            f"Code:\n{code}"
        )