import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path
import json

# Page configuration
st.set_page_config(
    page_title="SecureRAG Enterprise (v_0.1.0)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    .stApp {
        background-color: #f1f5f9;
        color: #0f172a;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    div[data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 16px !important;
        padding: 36px 32px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05) !important;
    }

    /* Header styling */
    .portal-header {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 4px;
        text-align: center;
    }
    
    .portal-subtitle {
        font-size: 0.88rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 24px;
    }
    
    /* Role Badges */
    .role-badge-c_level {
        background-color: #fef3c7;
        color: #b45309;
        border: 1px solid #fde68a;
        padding: 4px 12px;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
    }
    .role-badge-engineering {
        background-color: #eff6ff;
        color: #2563eb;
        border: 1px solid #bfdbfe;
        padding: 4px 12px;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .role-badge-hr {
        background-color: #f3e8ff;
        color: #9333ea;
        border: 1px solid #e9d5ff;
        padding: 4px 12px;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .role-badge-finance {
        background-color: #f0fdf4;
        color: #16a34a;
        border: 1px solid #bbf7d0;
        padding: 4px 12px;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .role-badge-marketing {
        background-color: #fff7ed;
        color: #ea580c;
        border: 1px solid #fed7aa;
        padding: 4px 12px;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .role-badge-general {
        background-color: #f3f4f6;
        color: #4b5563;
        border: 1px solid #e5e7eb;
        padding: 4px 12px;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Cost Dashboard Metric Card */
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .metric-title {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 1.2rem;
        font-weight: 800;
        color: #0f172a;
    }
    .alert-banner {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 10px;
    }

    /* File container styling */
    .file-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 8px;
    }
    .file-name {
        font-weight: 600;
        font-size: 0.85rem;
        color: #1e293b;
    }
    .file-meta {
        font-size: 0.72rem;
        color: #64748b;
        display: flex;
        justify-content: space-between;
        margin-top: 4px;
        align-items: center;
    }
    
    .ref-block {
        border-left: 3px solid #2563eb;
        background: #f0f9ff;
        padding: 8px 12px;
        margin: 6px 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.82rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "password" not in st.session_state:
    st.session_state.password = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

API_BASE_URL = "http://127.0.0.1:8000"

def get_role_badge_html(role: str) -> str:
    role_lower = role.lower()
    if "c_level" in role_lower or "exec" in role_lower:
        return f'<span class="role-badge-c_level">👑 {role.upper()}</span>'
    elif "eng" in role_lower:
        return f'<span class="role-badge-engineering">🔧 {role.upper()}</span>'
    elif "hr" in role_lower:
        return f'<span class="role-badge-hr">👥 {role.upper()}</span>'
    elif "finance" in role_lower or "fin" in role_lower:
        return f'<span class="role-badge-finance">💰 {role.upper()}</span>'
    elif "marketing" in role_lower or "mkt" in role_lower:
        return f'<span class="role-badge-marketing">📢 {role.upper()}</span>'
    else:
        return f'<span class="role-badge-general">🌐 {role.upper()}</span>'

# LOGIN SCREEN
if not st.session_state.authenticated:
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        with st.form("login_form", border=True):
            st.markdown("""
                <div style="text-align: center; margin-bottom: 16px;">
                    <div style="font-size: 2.8rem; line-height: 1; margin-bottom: 10px;">🛡️</div>
                    <h2 class="portal-header">SecureRAG Enterprise Portal</h2>
                    <p class="portal-subtitle">Role-Based Access • Guardrails • Cost Tracking • Monitoring</p>
                </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input("Username", placeholder="e.g., Nick, Natasha, Sam, Tony")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    try:
                        response = requests.get(
                            f"{API_BASE_URL}/login",
                            auth=HTTPBasicAuth(username, password)
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.session_state.password = password
                            st.session_state.role = data.get("role", "general")
                            st.session_state.messages = []
                            st.success("Successfully authenticated!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    except requests.exceptions.ConnectionError:
                        st.error("Backend server is not running. Please start the FastAPI server first!")
        
        # User credentials reference guide
        st.markdown("""
        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-top: 16px; font-size: 0.82rem;">
            <b>🔑 Demo Test Credentials:</b><br>
            • <b>Nick</b> / <code>execpass123</code> → 👑 <b>C-Level Executive</b> (Access All Data)<br>
            • <b>Sam</b> / <code>financepass</code> → 💰 <b>Finance Role</b><br>
            • <b>Natasha</b> / <code>hrpass123</code> → 👥 <b>HR Role</b><br>
            • <b>Tony</b> / <code>password123</code> → 🔧 <b>Engineering Role</b><br>
            • <b>Bruce</b> / <code>securepass</code> → 📢 <b>Marketing Role</b>
        </div>
        """, unsafe_allow_html=True)

# PORTAL MAIN INTERFACE
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"### Welcome, **{st.session_state.username}**!")
        badge_html = get_role_badge_html(st.session_state.role)
        st.markdown(f"**Security Profile:** {badge_html}", unsafe_allow_html=True)
        st.markdown("---")

        # -------------------------------------------------------------
        # COST & TOKEN MONITORING DASHBOARD (Sidebar Widget)
        # -------------------------------------------------------------
        st.markdown("### 💰 Token & Cost Monitoring")
        try:
            cost_resp = requests.get(f"{API_BASE_URL}/cost-metrics")
            if cost_resp.status_code == 200:
                metrics = cost_resp.json()
                
                # Check for budget alerts
                if metrics.get("alert_triggered", False):
                    st.markdown("""
                    <div class="alert-banner">
                        🚨 <b>COST ALERT TRIGGERED</b><br>
                        Budget limit exceeded! Total cost reached limit.
                    </div>
                    """, unsafe_allow_html=True)
                
                m1, m2 = st.columns(2)
                with m1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Total Queries</div>
                        <div class="metric-value">{metrics.get('total_queries', 0)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Total Cost (USD)</div>
                        <div class="metric-value">${metrics.get('total_cost_usd', 0.0):.4f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.caption(f"Tokens Used: **{metrics.get('total_tokens', 0):,}** (Prompt: {metrics.get('total_prompt_tokens', 0):,} | Output: {metrics.get('total_completion_tokens', 0):,})")
        except Exception:
            st.caption("Unable to fetch cost metrics backend.")

        st.markdown("---")
        
        # -------------------------------------------------------------
        # ACCESSIBLE KNOWLEDGE BASES (RBAC Dependent)
        # -------------------------------------------------------------
        st.markdown("### 📂 Accessible Knowledge Bases")
        data_dir = Path(__file__).parent / "resources" / "data"
        
        if st.session_state.role in ["c_level", "executive"]:
            allowed_folders = ["general", "engineering", "finance", "hr", "marketing"]
        else:
            allowed_folders = ["general"]
            if st.session_state.role and st.session_state.role != "general":
                allowed_folders.append(st.session_state.role)
            
        accessible_files = []
        for folder in allowed_folders:
            folder_path = data_dir / folder
            if folder_path.exists() and folder_path.is_dir():
                for f in folder_path.iterdir():
                    if f.is_file() and f.suffix in [".md", ".csv"]:
                        accessible_files.append({
                            "name": f.name,
                            "role": folder,
                            "size": f.stat().st_size
                        })
                        
        if accessible_files:
            for file_info in accessible_files:
                size_str = f"{file_info['size'] / 1024:.1f} KB" if file_info['size'] >= 1024 else f"{file_info['size']} bytes"
                role_label = get_role_badge_html(file_info['role'])
                st.markdown(f"""
                <div class="file-container">
                    <div class="file-name">📄 {file_info['name']}</div>
                    <div class="file-meta">
                        <span>{size_str}</span>
                        <span>{role_label}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No documents available for your current security role level.")
            
        st.markdown("---")
        
        # Action Buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("Log Out", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.session_state.password = ""
                st.session_state.role = ""
                st.session_state.messages = []
                st.rerun()

    # Main Header & Nav Tabs
    st.markdown('<h1 style="font-weight: 800; color: #0f172a;">🛡️ SecureRAG Enterprise</h1>', unsafe_allow_html=True)
    
    tab_chat, tab_evals = st.tabs(["💬 Assistant Chat", "📊 Continuous Evals & Monitoring"])
    
    with tab_evals:
        st.markdown("### 📊 Ragas & Continuous Deployment Evaluation Suite (v_0.1.0)")
        eval_report_file = Path(__file__).parent / "evals" / "eval_report.json"
        if eval_report_file.exists():
            with open(eval_report_file, "r", encoding="utf-8") as f:
                report = json.load(f)
                
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Total Test Cases", report.get("total_test_cases", 0))
            with col_b:
                st.metric("Security & RBAC Pass Rate", f"{report.get('pass_rate_percent', 0)}%")
            with col_c:
                st.metric("Last Run Timestamp", report.get("timestamp", "N/A")[:19].replace("T", " "))
                
            st.markdown("---")
            st.markdown("#### 🎯 RAGAS Evaluation Metrics Triad")
            ragas_data = report.get("ragas_summary", {})
            
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.metric("Overall Ragas Score", f"{ragas_data.get('overall_ragas_score', 0.0) * 100:.1f}%")
            with r2:
                st.metric("Faithfulness Score", f"{ragas_data.get('faithfulness', 0.0) * 100:.1f}%")
            with r3:
                st.metric("Answer Relevancy", f"{ragas_data.get('answer_relevancy', 0.0) * 100:.1f}%")
            with r4:
                st.metric("Context Precision", f"{ragas_data.get('context_precision', 0.0) * 100:.1f}%")

            st.markdown("---")
            st.markdown("#### Test Execution & Ragas Detailed Results")
            for res in report.get("test_results", []):
                status_icon = "✅ PASSED" if res["passed"] else "❌ FAILED"
                with st.expander(f"{status_icon} - TestCase: {res['name']}"):
                    if "ragas" in res:
                        rg = res["ragas"]
                        st.caption(f"🎯 **Ragas Scores** — Faithfulness: `{rg.get('faithfulness', 0):.2f}` | Relevancy: `{rg.get('answer_relevancy', 0):.2f}` | Context Precision: `{rg.get('context_precision', 0):.2f}`")
                    for note in res.get("notes", []):
                        st.write(f"• {note}")
        else:
            st.info("No evaluation report generated yet. Run `python evals/run_evals.py` to generate the test report.")

    with tab_chat:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Display Guardrails metadata if present
                if "guardrails" in message:
                    g = message["guardrails"]
                    if g.get("contains_pii", False):
                        st.caption(f"🔒 **Guardrail Action:** Sanitized PII Types: {', '.join(g.get('pii_types', []))}")
                
                # Display sources
                if "sources" in message and message["sources"]:
                    with st.expander("🔍 Verified References Used"):
                        for src in message["sources"]:
                            badge = get_role_badge_html(src["role"])
                            st.markdown(f"""
                            <div class="ref-block">
                                <b>Document:</b> {src['source']} | <b>Security Scope:</b> {badge}
                            </div>
                            """, unsafe_allow_html=True)
                            
                # Display cost for message
                if "cost_metrics" in message and message["cost_metrics"].get("total_tokens", 0) > 0:
                    c = message["cost_metrics"]
                    st.caption(f"⚡ *Cost: ${c.get('query_cost_usd', 0):.6f} | Tokens: {c.get('total_tokens', 0)}*")

        # Chat Input
        if prompt := st.chat_input("Ask a question about company data (Try testing PII or Out-of-Scope)..."):
            with st.chat_message("user"):
                st.write(prompt)
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                response_placeholder.markdown("*Processing guardrails & evaluating company knowledge base...*")
                
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/chat",
                        params={"message": prompt},
                        auth=HTTPBasicAuth(st.session_state.username, st.session_state.password)
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        answer = result.get("answer", "")
                        sources = result.get("sources", [])
                        guardrails = result.get("guardrails", {})
                        cost_metrics = result.get("cost_metrics", {})
                        
                        response_placeholder.write(answer)
                        
                        if guardrails.get("contains_pii", False):
                            st.caption(f"🔒 **Guardrail Action:** Sanitized PII Types: {', '.join(guardrails.get('pii_types', []))}")
                            
                        if sources:
                            with st.expander("🔍 Verified References Used"):
                                for src in sources:
                                    badge = get_role_badge_html(src["role"])
                                    st.markdown(f"""
                                    <div class="ref-block">
                                        <b>Document:</b> {src['source']} | <b>Security Scope:</b> {badge}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                        if cost_metrics.get("total_tokens", 0) > 0:
                            st.caption(f"⚡ *Cost: ${cost_metrics.get('query_cost_usd', 0):.6f} | Tokens: {cost_metrics.get('total_tokens', 0)}*")
                                    
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                            "guardrails": guardrails,
                            "cost_metrics": cost_metrics
                        })
                        
                        # Refresh interface to update sidebar cost metrics
                        st.rerun()
                        
                    else:
                        response_placeholder.error(f"Error ({response.status_code}): {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    response_placeholder.error(f"Failed to reach chatbot backend: {e}")
