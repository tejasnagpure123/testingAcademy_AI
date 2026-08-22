"""
QABuddy.ai — Claude-Inspired Streamlit Chat UI
Warm White & Cream aesthetic with Teal accents and editorial typography.
"""

import os
import sys
import requests
import streamlit as st
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# ─── Configuration ──────────────────────────────────────────

API_URL = os.getenv("API_URL", "http://localhost:8000")
APP_PASSWORD = os.getenv("APP_PASSWORD", "qabuddy2026")

# ─── Page Config ────────────────────────────────────────────

st.set_page_config(
    page_title="QABuddy.ai — QA Intelligence",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Claude-Inspired Custom CSS ─────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global App Background: Warm Cream/Oatmeal */
    .stApp {
        background-color: #FAF8F5;
        color: #1F1E1D;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container max-width for reading comfort */
    .block-container {
        max-width: 960px !important;
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }

    /* Sidebar: Soft Warm Cream */
    section[data-testid="stSidebar"] {
        background-color: #F4EFE6 !important;
        border-right: 1px solid #E6DFD3 !important;
    }

    section[data-testid="stSidebar"] * {
        color: #2D2B28 !important;
    }

    /* Header styling with Claude Serif */
    .claude-header-container {
        text-align: center;
        padding: 1.5rem 0 1rem 0;
        margin-bottom: 1.5rem;
    }

    .claude-title {
        font-family: 'Newsreader', Georgia, serif;
        font-size: 2.75rem;
        font-weight: 500;
        color: #1F1E1D;
        letter-spacing: -0.02em;
        margin: 0;
        line-height: 1.2;
    }

    .claude-title span.teal {
        color: #0D9488;
        font-style: italic;
    }

    .claude-subtitle {
        font-size: 0.95rem;
        color: #6B6966;
        margin-top: 0.5rem;
        font-weight: 400;
    }

    /* Chat Messages */
    .stChatMessage {
        background: transparent !important;
        border: none !important;
        padding: 0.8rem 0 !important;
    }

    /* User message bubble */
    [data-testid="stChatMessage"]:has([data-testid="stChatAvatarUser"]) {
        background-color: #F2ECE1 !important;
        border-radius: 18px !important;
        padding: 1rem 1.25rem !important;
        margin-left: 15% !important;
        border: 1px solid #E5DDCF !important;
    }

    /* Assistant message container */
    [data-testid="stChatMessage"]:has([data-testid="stChatAvatarAssistant"]) {
        background-color: #FFFFFF !important;
        border-radius: 18px !important;
        padding: 1.35rem 1.65rem !important;
        margin-right: 3% !important;
        border: 1px solid #EAE5DC !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03) !important;
    }

    /* Typography inside messages */
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
        font-size: 0.96rem !important;
        line-height: 1.65 !important;
        color: #2D2B28 !important;
    }

    [data-testid="stChatMessage"] h1, [data-testid="stChatMessage"] h2, [data-testid="stChatMessage"] h3 {
        font-family: 'Newsreader', Georgia, serif !important;
        color: #1F1E1D !important;
        font-weight: 600 !important;
    }

    /* Code blocks */
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 6px !important;
    }

    p code {
        background-color: #EFE9DF !important;
        color: #0F766E !important;
        padding: 0.15rem 0.35rem !important;
        font-size: 0.88em !important;
    }

    pre code {
        background-color: #1E1E1E !important;
        color: #F8FAFC !important;
        padding: 1rem !important;
    }

    /* Main area suggested prompt buttons: Claude.ai white cards with teal hover */
    div[data-testid="stMainBlockContainer"] div.stButton > button {
        background-color: #FFFFFF !important;
        color: #1F1E1D !important;
        border: 1.2px solid #E5DFD5 !important;
        border-radius: 12px !important;
        padding: 0.85rem 1.1rem !important;
        text-align: left !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    div[data-testid="stMainBlockContainer"] div.stButton > button:hover {
        background-color: #FAFAF8 !important;
        border-color: #0D9488 !important;
        color: #0F766E !important;
        box-shadow: 0 4px 12px rgba(13, 148, 136, 0.08) !important;
        transform: translateY(-1px) !important;
    }

    /* Sidebar buttons styling */
    section[data-testid="stSidebar"] div.stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.84rem !important;
        transition: all 0.2s ease !important;
    }

    /* Source Citation Cards */
    .source-card {
        background: #F0FDFA;
        border: 1px solid #CCFBF1;
        border-left: 3px solid #0D9488;
        border-radius: 8px;
        padding: 0.6rem 0.85rem;
        margin: 0.4rem 0;
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .source-label {
        font-weight: 600;
        color: #0F766E;
    }

    .source-type-pill {
        background: #E6DFD3;
        color: #57534E;
        font-size: 0.72rem;
        padding: 0.15rem 0.45rem;
        border-radius: 10px;
        margin-left: 0.5rem;
    }

    .source-score-pill {
        background: #0D9488;
        color: #FFFFFF;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 10px;
    }

    /* Filter Active Pill */
    .filter-badge {
        display: inline-flex;
        align-items: center;
        background: #F0FDFA;
        color: #0F766E;
        border: 1px solid #99F6E4;
        padding: 0.3rem 0.85rem;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }

    /* Sidebar Status Cards */
    .status-card {
        background: #FFFFFF;
        border: 1px solid #E6DFD3;
        border-radius: 10px;
        padding: 0.85rem;
        margin-bottom: 0.75rem;
    }

    .status-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.84rem;
        padding: 0.25rem 0;
        border-bottom: 1px solid #F4EFE6;
    }

    .status-item:last-child {
        border-bottom: none;
    }

    .status-val-pill {
        background: #F0FDFA;
        color: #0F766E;
        font-weight: 600;
        font-size: 0.78rem;
        padding: 0.1rem 0.45rem;
        border-radius: 8px;
        border: 1px solid #CCFBF1;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        font-size: 0.88rem !important;
        color: #2D2B28 !important;
        border: 1px solid #E6DFD3 !important;
    }

    /* Chat input box styling */
    [data-testid="stChatInput"] {
        background-color: #FAF8F5 !important;
    }

    [data-testid="stChatInput"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #D8D2C5 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
    }

    [data-testid="stChatInput"] > div:focus-within {
        border-color: #0D9488 !important;
        box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.12) !important;
    }

    /* Login Card */
    .login-box {
        background: #FFFFFF;
        border: 1px solid #E6DFD3;
        border-radius: 18px;
        padding: 2.5rem 2rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Authentication ─────────────────────────────────────────

def check_auth():
    """Claude-styled authentication card."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("""
        <div class="claude-header-container" style="margin-top: 3rem;">
            <h1 class="claude-title">QABuddy<span class="teal">.ai</span></h1>
            <p class="claude-subtitle">Autonomous Hybrid QA Knowledge System</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1.8, 1])
        with col2:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.markdown("<h3 style='font-family:Newsreader,serif; margin-top:0; color:#1F1E1D;'>Welcome back</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color:#787571; font-size:0.88rem; margin-bottom:1.5rem;'>Enter the workspace access key to explore grounded QA intelligence.</p>", unsafe_allow_html=True)
            
            password = st.text_input("Access Password", type="password", key="login_pw", placeholder="Enter password...")
            if st.button("Unlock QABuddy →", use_container_width=True):
                if password == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Please verify your credentials.")
            st.markdown('</div>', unsafe_allow_html=True)
        return False

    return True


# ─── API Helpers ────────────────────────────────────────────

def api_chat(question: str, source_filter: str = None, chat_history: list = None) -> dict:
    """Send a question to the QABuddy API."""
    payload = {"question": question}
    if source_filter:
        payload["source_filter"] = source_filter
    if chat_history:
        payload["chat_history"] = chat_history

    try:
        response = requests.post(f"{API_URL}/api/chat", json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to QABuddy API server. Please check that FastAPI is running on port 8000."}
    except Exception as e:
        return {"error": str(e)}


def api_health() -> dict:
    """Check API health."""
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=5)
        return response.json()
    except Exception:
        return {"status": "unreachable", "qdrant_status": "unknown", "collection_info": {}}


def api_ingest(sources: list = None, recreate: bool = False) -> dict:
    """Trigger ingestion."""
    try:
        response = requests.post(
            f"{API_URL}/api/ingest",
            json={"sources": sources, "recreate_collection": recreate},
            timeout=600,
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ─── Sidebar ────────────────────────────────────────────────

def render_sidebar():
    """Render Claude-styled warm sidebar with controls and system status."""
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.5rem 0 1rem 0;">
            <div style="font-family:'Newsreader',serif; font-size:1.4rem; font-weight:600; color:#1F1E1D;">
                QABuddy<span style="color:#0D9488; font-style:italic;">.ai</span>
            </div>
            <div style="font-size:0.75rem; color:#787571;">QA Hybrid RAG Assistant</div>
        </div>
        """, unsafe_allow_html=True)

        # Source filter
        source_options = [
            "All Sources",
            "selenium_repo",
            "playwright_repo",
            "test_cases",
            "jira_tickets",
            "company_docs",
            "meeting_transcripts",
            "lucid_charts",
            "prd_docs",
            "jenkins_logs",
        ]

        selected_source = st.selectbox(
            "Filter Knowledge Domain",
            source_options,
            index=0,
            help="Restrict retrieval to a specific data source",
        )

        st.session_state.source_filter = None if selected_source == "All Sources" else selected_source

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

        # System health card
        st.markdown("<div style='font-size:0.8rem; font-weight:600; text-transform:uppercase; color:#787571; margin-bottom:0.4rem; letter-spacing:0.04em;'>System Status</div>", unsafe_allow_html=True)
        health = api_health()
        status_text = health.get("status", "unknown")
        is_healthy = status_text == "healthy"
        points_count = health.get("collection_info", {}).get("points_count", 0)

        st.markdown(f"""
        <div class="status-card">
            <div class="status-item">
                <span style="color:#57534E;">Backend API</span>
                <span class="status-val-pill">{'🟢 Active' if is_healthy else '🔴 Offline'}</span>
            </div>
            <div class="status-item">
                <span style="color:#57534E;">Vector Store</span>
                <span class="status-val-pill">Qdrant</span>
            </div>
            <div class="status-item">
                <span style="color:#57534E;">Indexed Units</span>
                <span class="status-val-pill">{points_count:,} chunks</span>
            </div>
            <div class="status-item">
                <span style="color:#57534E;">Embedding</span>
                <span class="status-val-pill">BGE-M3 (Hybrid)</span>
            </div>
            <div class="status-item">
                <span style="color:#57534E;">Reranker</span>
                <span class="status-val-pill">BGE-Reranker-v2</span>
            </div>
            <div class="status-item">
                <span style="color:#57534E;">LLM</span>
                <span class="status-val-pill">Gemini 2.5 Flash</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Ingestion actions
        st.markdown("<div style='font-size:0.8rem; font-weight:600; text-transform:uppercase; color:#787571; margin:1rem 0 0.4rem 0; letter-spacing:0.04em;'>Data Management</div>", unsafe_allow_html=True)
        if st.button("⚡ Re-index Sources", use_container_width=True):
            with st.spinner("Ingesting and indexing sources..."):
                result = api_ingest()
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(f"Indexed {result.get('total_chunks', 0)} chunks!")
                    st.rerun()

        # Session actions
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🗑️ Clear", use_container_width=True, help="Clear conversation"):
                st.session_state.messages = []
                st.rerun()
        with col_b:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.rerun()


# ─── Main Chat Interface ───────────────────────────────────

def render_chat():
    """Render the main Claude-inspired chat interface."""
    # Top Header
    st.markdown("""
    <div class="claude-header-container">
        <h1 class="claude-title">Good morning, <span class="teal">QA Engineer</span></h1>
        <p class="claude-subtitle">Ask anything grounded in your frameworks, test repositories, JIRA tickets, and PRDs.</p>
    </div>
    """, unsafe_allow_html=True)

    # Active filter indicator
    if st.session_state.get("source_filter"):
        st.markdown(
            f'<div class="filter-badge">🔍 Domain Filter: <strong>{st.session_state.source_filter}</strong></div>',
            unsafe_allow_html=True,
        )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Prompt Starters (show when no messages yet)
    if not st.session_state.messages:
        st.markdown("<div style='font-size:0.82rem; font-weight:600; color:#787571; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.04em;'>Suggested Prompts</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧩 Selenium BaseTest & DriverManager", use_container_width=True):
                st.session_state.pending_prompt = "Explain how the BaseTest class is structured and how DriverManager handles WebDriver lifecycle in our Selenium framework."
                st.rerun()
            if st.button("📋 KAN-13 Acceptance Criteria", use_container_width=True):
                st.session_state.pending_prompt = "What are the functional requirements and acceptance criteria specified in ticket KAN-13?"
                st.rerun()

        with col2:
            if st.button("🔍 Analyze Jenkins Log Failure", use_container_width=True):
                st.session_state.pending_prompt = "What caused the test failure in the Jenkins build log? Explain the stack trace."
                st.rerun()
            if st.button("🎭 Playwright Headless Configuration", use_container_width=True):
                st.session_state.pending_prompt = "How do we configure headless mode and test runners in our Playwright framework?"
                st.rerun()

    # Handle pending prompt from starter buttons
    incoming_prompt = None
    if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
        incoming_prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None

    # Display chat history
    for message in st.session_state.messages:
        avatar_icon = "👤" if message["role"] == "user" else "✨"
        with st.chat_message(message["role"], avatar=avatar_icon):
            st.markdown(message["content"])

            # Show sources if available
            if message.get("sources"):
                with st.expander("📚 Cited Knowledge Sources", expanded=False):
                    for src in message["sources"]:
                        source_label = src.get("ticket_key") or src.get("source_file", "Unknown")
                        source_type = src.get("source_type", "")
                        score = src.get("score", 0)
                        st.markdown(
                            f'<div class="source-card">'
                            f'<div>'
                            f'<span class="source-label">📄 {source_label}</span>'
                            f'<span class="source-type-pill">{source_type}</span>'
                            f'</div>'
                            f'<span class="source-score-pill">Match: {score:.3f}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

    # Chat input
    chat_prompt = st.chat_input("Ask QABuddy anything about your QA workspace...")
    prompt = incoming_prompt or chat_prompt

    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Get response from QA Chain
        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("Searching multi-source index & synthesizing grounded answer..."):
                chat_history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                ]

                result = api_chat(
                    question=prompt,
                    source_filter=st.session_state.get("source_filter"),
                    chat_history=chat_history[-6:] if chat_history else None,
                )

                if "error" in result:
                    st.error(f"⚠️ {result['error']}")
                    answer = f"Error: {result['error']}"
                    sources = []
                else:
                    answer = result.get("answer", "No answer generated")
                    sources = result.get("sources", [])

                    st.markdown(answer)

                    # Display cited source cards
                    if sources:
                        with st.expander("📚 Cited Knowledge Sources", expanded=False):
                            for src in sources:
                                source_label = src.get("ticket_key") or src.get("source_file", "Unknown")
                                source_type = src.get("source_type", "")
                                score = src.get("score", 0)
                                st.markdown(
                                    f'<div class="source-card">'
                                    f'<div>'
                                    f'<span class="source-label">📄 {source_label}</span>'
                                    f'<span class="source-type-pill">{source_type}</span>'
                                    f'</div>'
                                    f'<span class="source-score-pill">Match: {score:.3f}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )

                        retrieved = result.get("num_chunks_retrieved", 0)
                        reranked = result.get("num_chunks_reranked", 0)
                        st.caption(f"⚡ Retrieved {retrieved} candidates → Cross-encoder reranked to {reranked} cited sources")

                # Save to session history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })


# ─── Main ───────────────────────────────────────────────────

def main():
    if check_auth():
        render_sidebar()
        render_chat()


if __name__ == "__main__":
    main()
