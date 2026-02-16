from core.llm_provider import HybridLLMProvider
from core.protocol import TaskResult, AgentMessage
from agents.base_agent import BaseAgent
from utils.validators import validate_python_syntax
from config import Config

class ManagerAgent:
    def __init__(self, llm_provider: HybridLLMProvider, agents: dict):
        self.llm = llm_provider
        self.agents = agents
        self.history = []

    def _run_with_self_healing(self, agent_name: str, payload: dict) -> TaskResult:
        """
        Executes an agent with a retry loop. 
        If the agent returns syntax errors or invalid JSON, it retries.
        """
        agent = self.agents[agent_name]
        last_result = None
        retry_count = 0
        
        while retry_count <= Config.MAX_RETRIES:
            # If retrying, construct context with previous errors
            retry_context = None
            if last_result and not last_result.success:
                errors = ", ".join(last_result.syntax_errors)
                if last_result.error_message:
                    errors += f" | {last_result.error_message}"
                retry_context = f"Previous attempt failed with errors: {errors}. Please correct the code and logic."

            # Execute
            result = agent.execute(payload, retry_context)
            self.history.append(result)
            
            # --- DEBUGGING: Print detailed error immediately ---
            if not result.success:
                print(f"\n--- ❌ AGENT FAILURE ({agent_name}) - Attempt {retry_count + 1} ---")
                print(f"Error Message: {result.error_message}")
                if result.data and 'raw_response' in result.data:
                    print(f"Raw AI Output (First 500 chars): {str(result.data['raw_response'])[:500]}")
                print(f"-------------------------------------------\n")
            
            # --- HEALING CHECK ---
            # 1. Check explicit 'success: false' in agent response
            if not result.success:
                last_result = result
                retry_count += 1
                continue
            
            # 2. Check for Syntax Errors in generated code (if code exists)
            code_to_check = result.data.get("code")
            if code_to_check:
                is_valid, syntax_errors = validate_python_syntax(code_to_check)
                if not is_valid:
                    # Inject syntax errors into result for the next retry prompt
                    result.success = False
                    result.syntax_errors = syntax_errors
                    last_result = result
                    retry_count += 1
                    continue
            
            # If we are here, the task passed validation
            return result

        # Max retries reached
        # Return the last result which contains the specific error details
        return TaskResult(
            success=False,
            error_message=f"CRITICAL: Agent {agent_name} failed after {Config.MAX_RETRIES} retries. Last Error: {last_result.error_message if last_result else 'Unknown'}",
            syntax_errors=last_result.syntax_errors if last_result else [],
            data=last_result.data if last_result else {}, # Pass raw data up for debugging
            sender="Manager"
        )

    def orchestrate_refactoring(self, legacy_code: str) -> dict:
        """Main pipeline workflow."""
        
        # Step 1: Architect
        print("[Manager] Dispatching Architect...")
        arch_payload = {"legacy_code": legacy_code}
        arch_result = self._run_with_self_healing("architect", arch_payload)
        
        if not arch_result.success:
            return {"status": "failed_at_architect", "result": arch_result}
        
        # Step 2: Builder
        print("[Manager] Dispatching Builder...")
        builder_payload = {
            "legacy_code": legacy_code,
            "plan": arch_result.data.get("plan", "")
        }
        build_result = self._run_with_self_healing("builder", builder_payload)
        
        if not build_result.success:
            return {"status": "failed_at_builder", "result": build_result}
            
        modernized_code = build_result.data.get("code")

        # Step 3: QA
        print("[Manager] Dispatching QA...")
        qa_payload = {"code": modernized_code}
        qa_result = self._run_with_self_healing("qa", qa_payload)
        
        if not qa_result.success:
            return {"status": "failed_at_qa", "result": qa_result}

        # Step 4: Librarian
        print("[Manager] Dispatching Librarian...")
        librarian_payload = {"code": modernized_code}
        doc_result = self._run_with_self_healing("librarian", librarian_payload)

        return {
            "status": "success",
            "modernized_code": modernized_code,
            "documentation": doc_result.data,
            "qa_report": qa_result.data
        }