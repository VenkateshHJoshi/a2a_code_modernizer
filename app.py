import streamlit as st
import sys
import os
import subprocess
import tempfile
import time
import json
import shutil
from datetime import datetime
import socket

# Add the root directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports
from core.llm_provider import HybridLLMProvider
from core.model_manager import ModelManager
from core.protocol import TaskResult
from agents.manager import ManagerAgent
from agents.architect import ArchitectAgent
from agents.builder import BuilderAgent
from agents.qa import QAAgent
from agents.librarian import LibrarianAgent
from config import Config

# --- Page Config ---
st.set_page_config(page_title="A2A Code Modernizer", page_icon="🤖", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    .stButton>button { color: white; background-color: #4CAF50; border-radius: 5px; width: 100%; }
    .stButton>button[kind="secondary"] { background-color: #ff4b4b; width: 100%; }
    .test-btn { background-color: #2196F3; color: white; border: none; padding: 5px 10px; border-radius: 4px; width: auto; display: inline-block; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- Session State ---
defaults = {
    'mode': None, 
    'ollama_running': False, 
    'qwen_available': False, 
    'api_key': "", 
    'pipeline_run': False, 
    'manager': None,
    'legacy_code': ""
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# --- Helpers ---

def check_ollama_server():
    try:
        sock = socket.create_connection(("127.0.0.1", 11434), timeout=2)
        sock.close()
        return True
    except: return False

def run_code_snippet(code: str, is_test_case=False):
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, "test_script.py")
    try:
        with open(temp_file, 'w') as f: f.write(code)
        result = subprocess.run([sys.executable, temp_file], capture_output=True, text=True, timeout=10)
        return result.stdout, result.stderr, None
    except subprocess.TimeoutExpired:
        return None, None, "Execution timed out."
    except Exception as e:
        return None, None, str(e)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def generate_report(history, final_result):
    report = f"# Code Modernization Report\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Architect
    plan_text = "No plan generated."
    for item in history:
        if item.sender == "Architect" and item.data:
            plan_text = item.data.get("plan") or item.data.get("analysis") or str(item.data)
            break
    report += "## 1. Architect Analysis\n" + str(plan_text) + "\n\n"
    
    # Code
    code = final_result.get("modernized_code", "")
    report += "## 2. Modernized Code\n```python\n" + code + "\n```\n\n"
    
    # QA
    qa_data = final_result.get("qa_report", {})
    review = qa_data.get("review", "No review.")
    report += "## 3. QA Report\n**Review:** " + str(review) + "\n\n"
    
    tests = qa_data.get("test_cases", [])
    if tests:
        report += "### Generated Test Cases\n"
        for t in tests:
            report += f"- **{t.get('name', 'Test')}**: `{t.get('code', '')[:50]}...`\n"
    
    # Docs
    doc_data = final_result.get('documentation', {})
    if not isinstance(doc_data, dict): doc_data = {}
    doc_text = doc_data.get("documentation", "No docs.")
    report += "## 4. Documentation\n" + str(doc_text)
    
    return report

# --- Sidebar & Setup ---
st.title("🚀 Distributed Agent-to-Agent (A2A) Code Modernizer")
st.markdown("---")

# 1. Mode Selection
if st.session_state.mode is None:
    st.subheader("Step 1: Select Processing Mode")
    c1, c2 = st.columns(2)
    if c1.button("🖥️ Local (Ollama)", use_container_width=True):
        st.session_state.mode = 'local'; st.rerun()
    if c2.button("☁️ Cloud (Gemini)", use_container_width=True):
        st.session_state.mode = 'cloud'; st.rerun()

# --- LOCAL MODE ---
elif st.session_state.mode == 'local':
    st.sidebar.header("Local Environment")
    if not st.session_state.ollama_running:
        st.info("🔍 Scanning Port 11434...")
        if check_ollama_server():
            st.session_state.ollama_running = True
            st.sidebar.success("✅ Ollama Connected")
            st.rerun()
        else:
            st.error("❌ Ollama Server is NOT running.")
            st.markdown("1. Open terminal.\n2. Run: `ollama serve`\n3. Click Done.")
            if st.button("✅ Done, Check Connection"): st.rerun()
            st.stop()
    if not st.session_state.qwen_available:
        st.sidebar.success("✅ Ollama: Connected")
        if ModelManager.check_model_availability(Config.LOCAL_MODEL_NAME):
            st.session_state.qwen_available = True
            st.success(f"✅ Model Ready!")
            st.rerun()
        else:
            st.warning(f"⚠️ Model Missing.")
            if st.button(f"⬇️ Download {Config.LOCAL_MODEL_NAME}", type="primary"):
                with st.spinner("Downloading..."):
                    success, msg = ModelManager.pull_model(Config.LOCAL_MODEL_NAME)
                    if success:
                        st.session_state.qwen_available = True
                        st.success("Downloaded!"); time.sleep(1); st.rerun()
                    else:
                        st.error(msg)
                        st.code(f"ollama pull {Config.LOCAL_MODEL_NAME}")
                        if st.button("🔄 Refresh"): st.rerun()
            st.stop()
    st.sidebar.success("✅ System Ready (Local)")

# --- CLOUD MODE ---
elif st.session_state.mode == 'cloud':
    st.sidebar.header("Cloud Config")
    if not st.session_state.api_key:
        k = st.text_input("Gemini API Key", type="password")
        if st.button("Connect"):
            if k:
                st.session_state.api_key = k
                os.environ["GEMINI_API_KEY"] = k
                st.success("Connected"); st.rerun()
            else: st.warning("Enter Key")
        st.stop()
    else: st.sidebar.success("✅ System Ready (Cloud)")

# --- MAIN PIPELINE ---
if (st.session_state.mode == 'local' and st.session_state.qwen_available) or \
   (st.session_state.mode == 'cloud' and st.session_state.api_key):

    st.header("Step 2: Input Legacy Code")
    legacy_code = st.text_area("Paste Python Code:", height=200, placeholder="def old_code(): pass")
    
    if st.button("🚀 Run Modernization Pipeline", type="primary", use_container_width=True):
        if not legacy_code.strip():
            st.warning("Please enter code first.")
        else:
            st.session_state.legacy_code = legacy_code
            
            # Force mode selection
            llm_provider = HybridLLMProvider(force_mode=st.session_state.mode)
            
            agents = {
                "architect": ArchitectAgent(llm_provider, "Architect", Config.ARCHITECT_SYSTEM_PROMPT),
                "builder": BuilderAgent(llm_provider, "Builder", Config.BUILDER_SYSTEM_PROMPT),
                "qa": QAAgent(llm_provider, "QA", Config.QA_SYSTEM_PROMPT),
                "librarian": LibrarianAgent(llm_provider, "Librarian", Config.LIBRARIAN_SYSTEM_PROMPT)
            }
            manager = ManagerAgent(llm_provider, agents)
            
            with st.status("Initializing Agents...", expanded=True) as status:
                
                # 1. Architect
                status.update(label="🏗️ Architect: Analyzing...", state="running")
                arch_result = manager._run_with_self_healing("architect", {"legacy_code": legacy_code})
                
                if not arch_result.success:
                    status.update(label="❌ Architect Failed", state="error")
                    st.error("Architecture Analysis Failed")
                    st.markdown(f"**Error:** {arch_result.error_message}")
                    if arch_result.data and "raw_response" in arch_result.data:
                        st.subheader("Raw AI Response (Debug)")
                        st.text_area("Output", arch_result.data["raw_response"], height=200)
                    st.stop()
                    
                status.update(label="✅ Architect: Plan Created", state="complete", expanded=False)
                
                # 2. Builder
                status.update(label="🔨 Builder: Refactoring...", state="running")
                plan = arch_result.data.get("plan", "Improve code.")
                build_result = manager._run_with_self_healing("builder", {"legacy_code": legacy_code, "plan": plan})
                
                if not build_result.success:
                    status.update(label="❌ Builder Failed", state="error")
                    st.error("Code Refactoring Failed")
                    st.markdown(f"**Error:** {build_result.error_message}")
                    if build_result.data and "raw_response" in build_result.data:
                        st.text_area("Raw Response", build_result.data["raw_response"], height=200)
                    st.stop()
                    
                modern_code = build_result.data.get("code")
                status.update(label="✅ Builder: Code Refactored", state="complete", expanded=False)

                # 3. QA
                status.update(label="🛡️ QA: Validating & Testing...", state="running")
                qa_result = manager._run_with_self_healing("qa", {"code": modern_code})
                if not qa_result.success: 
                    status.update(label="⚠️ QA: Issues Found", state="running")
                else: 
                    status.update(label="✅ QA: Validation Passed", state="complete", expanded=False)

                # 4. Librarian
                status.update(label="📚 Librarian: Writing Docs...", state="running")
                doc_result = manager._run_with_self_healing("librarian", {"code": modern_code})
                final_doc_data = doc_result.data if isinstance(doc_result.data, dict) else {}
                status.update(label="✅ Librarian: Docs Generated", state="complete")
            
            st.session_state.final_result = {
                "status": "success",
                "modernized_code": modern_code,
                "documentation": final_doc_data,
                "qa_report": qa_result.data
            }
            st.session_state.manager = manager
            st.session_state.pipeline_run = True
            st.rerun()

    # --- RESULTS UI ---
    if st.session_state.pipeline_run:
        result = st.session_state.final_result
        modern_code = result.get('modernized_code', '')
        original_code = st.session_state.legacy_code
        
        # 1. ARCHITECT PLAN
        st.header("🏗️ Architect's Plan")
        plan_text = "No plan found."
        for h in st.session_state.manager.history:
            if h.sender == "Architect" and h.data:
                plan_text = h.data.get("plan") or str(h.data)
                break
        st.info(plan_text)

        st.markdown("---")

        # 2. CODE COMPARISON
        st.header("💻 Code Comparison")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Code")
            st.code(original_code, language='python', line_numbers=True)
            if st.button("▶️ Run Original Code", key="run_orig"):
                with st.spinner("Running Original..."):
                    out, err, exc = run_code_snippet(original_code)
                    if exc: st.error(exc)
                    if err: st.code(err, language='bash')
                    if out: st.success("Output:"); st.code(out, language='text')

        with col2:
            st.subheader("Modernized Code")
            st.code(modern_code, language='python', line_numbers=True)
            if st.button("▶️ Run Modernized Code", key="run_mod"):
                with st.spinner("Running Modernized..."):
                    out, err, exc = run_code_snippet(modern_code)
                    if exc: st.error(exc)
                    if err: st.code(err, language='bash')
                    if out: st.success("Output:"); st.code(out, language='text')

        st.markdown("---")

        # 3. QA & TEST SUITE
        st.header("🛡️ QA Analysis & Test Suite")
        qa_data = result.get('qa_report', {})
        
        if st.checkbox("🐞 Debug QA Data"):
            st.json(qa_data)

        st.info(f"**Review:** {qa_data.get('review', 'No review.')}")
        
        test_cases = qa_data.get('test_cases', [])
        if test_cases:
            st.markdown("### 🧪 Generated Test Cases")
            for i, t in enumerate(test_cases):
                with st.expander(f"Test Case {i+1}: {t.get('name', 'Unnamed Test')}", expanded=False):
                    code_snippet = t.get('code', '')
                    st.code(code_snippet, language='python')
                    if st.button(f"Run Test {i+1}", key=f"test_{i}"):
                        with st.spinner(f"Running Test {i+1}..."):
                            out, err, exc = run_code_snippet(code_snippet)
                            if exc: st.error(exc)
                            if err: st.code(err, language='bash')
                            if out: st.success("Test Output:"); st.code(out, language='text')
        else:
            st.warning("No test cases generated by QA Agent.")
            if not qa_data:
                st.error("QA Agent returned no data at all.")
            else:
                st.write("QA Agent returned these keys:", list(qa_data.keys()))

        st.markdown("---")

        # 4. DOCUMENTATION
        st.header("📚 Documentation Preview")
        doc_data = result.get('documentation')
        if doc_data and isinstance(doc_data, dict):
            doc_text = doc_data.get('documentation', 'No docs.')
            st.markdown(doc_text)
        else:
            st.markdown("*No documentation available.*")

        # 5. EXPORT
        st.header("📥 Export")
        rep = generate_report(st.session_state.manager.history, result)
        st.download_button("Download Full Report", rep, "report.md", "text/markdown")