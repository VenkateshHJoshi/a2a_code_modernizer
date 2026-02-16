from agents.base_agent import BaseAgent

class QAAgent(BaseAgent):
    def get_task_prompt(self, payload: dict) -> str:
        code = payload.get("code", "")
        return (
            "Review the provided Python code for logic errors, security issues, and incomplete implementation. "
            "Verify it is syntactically correct and runnable. "
            "If there are issues, set 'success' to false and list them in 'error_message'. "
            "If code is perfect, set 'success' to true.\n"
            "JSON Format: { 'success': boolean, 'data': { 'review': 'summary' }, 'error_message': 'string if failed' }.\n\n"
            f"Code:\n{code}"
        )