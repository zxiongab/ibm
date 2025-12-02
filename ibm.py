"""
EPLC Assistant - Streamlit Frontend
Enterprise Product Lifecycle Documentation Assistant
"""

import streamlit as st
import json
import os
from backend_api import EPLCBackend



# ============================================================================
# PAGE CONFIGURATION - MUST BE FIRST STREAMLIT COMMAND
# ============================================================================
st.set_page_config(
    page_title="EPLC Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- Hide Deploy button only ---
hide_deploy_only = """
<style>
button[kind="header"] {display: none;}
</style>
"""
st.markdown(hide_deploy_only, unsafe_allow_html=True)
# ============================================================================
# BACKEND INITIALIZATION WITH CACHING
# ============================================================================
@st.cache_resource
def get_backend():
    """Initialize backend with error handling and caching"""
    try:
        return EPLCBackend()
    except Exception as e:
        st.error(f"❌ Failed to initialize backend: {str(e)}")
        st.info("💡 Make sure your .env file contains OPENAI_API_KEY and vector_db folders exist")
        return None

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================
st.markdown(
    """
<style>
    /* ================= Global Styles ================= */
    .main-header { font-size: 2.5rem; font-weight: 800; text-align: center; color: #111827; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; text-align: center; color: #6b7280; max-width: 800px; margin: 0 auto 3rem auto; line-height: 1.6; }

    /* ================= Card Styles ================= */
    .feature-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 0; /* Padding handled internally */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        height: 100%;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        margin-top: -17px !important;
    }
    
    .card-header-bg {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 24px;
        border-bottom: 1px solid #e0e7ff;
    }

    .card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2937;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .card-body {
        padding: 24px;
        flex-grow: 1;
    }

    /* ================= Step List Styles ================= */
    .step-item {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
        align-items: flex-start;
    }

    .step-icon {
        flex-shrink: 0;
        width: 32px;
        height: 32px;
        background-color: #e0f2fe;
        color: #0369a1;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
        border: 1px solid #dbeafe;
    }

    .step-content h4 {
        margin: 0 0 4px 0;
        font-size: 17px;
        font-weight: 600;
        color: #1f2937;
    }

    .step-content p {
        margin: 0;
        font-size: 15px;
        color: #4b5563;
        line-height: 1.5;
    }



    /* ================= Sidebar styles ================= */
    .sidebar-header {
        font-size: 1.8rem;
        font-weight: bold;
        text-align: left;
        margin-bottom: 0.5rem;
        color: #1f1f1f;
    }
    .sidebar-subheader {
        font-size: 1rem;
        text-align: left;
        margin-bottom: 2rem;
        color: #666;
        line-height: 1.4;
    }
    /* Sidebar 背景色 */
    section[data-testid="stSidebar"] {
        background-color: #fcfcfd !important;  /* 或 #e0f2fe，看你喜欢哪种浅蓝 */
    }

    /* ===== Sidebar 未选中按钮显示成“纯文字” ===== */
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #4b5563 !important;         /* 灰色文字 */
        text-align: left !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        border-radius: 0 !important;
    }

    /* hover 时稍微变深一点，像可点击文字 */
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background-color: transparent !important;
        color: #111827 !important;

    }

    /* ===== Sidebar 选中项（primary）保持 pill 按钮样式 ===== */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #e0f2fe !important;
        border-color: #e0f2fe !important;
        color: #111827 !important;
        border-radius: 9999px !important;
        font-weight: 600 !important;
        text-align: left !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
                0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        width: 100% !important;
        white-space: nowrap !important;
    }

    /* 让 sidebar 按钮占满整行 + 左对齐 */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        width: 100% !important;
        text-align: left !important;     /* ---- 关键：左对齐文字 ---- */
        justify-content: flex-start !important; /* 兼容不同浏览器 */
        padding-left: 14px !important;   /* 更好看的左边距 */
        padding-right: 14px !important;
    }

    /* ========= 主内容区域的 CTA 按钮：做成和 sidebar 类似的 pill ========= */
    section[data-testid="stMain"] .stButton > button[kind="primary"] {
        border-radius: 9999px !important;   /* pill 形状 */
        width: 100% !important;            /* 占满卡片底部一行，和你现在布局一致 */
        padding-top: 0.75rem !important;
        padding-bottom: 0.75rem !important;
        font-weight: 500 !important;
        text-align: center !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
                0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }

    /* ===== 主内容区域 CTA 按钮字体改成黑色 ===== */
    section[data-testid="stMain"] .stButton > button[kind="primary"] {
        color: #1f2937 !important;  /* 深灰接近黑色，视觉舒服 */
    }


/* ===========================================
   GLOBAL BUTTON DESIGN SYSTEM
   Primary & Secondary unified pill UI
=========================================== */

/* 基础：所有按钮统一 pill 与尺寸 */
.stButton > button,
.stDownloadButton > button,
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-secondary"] {
    border-radius: 9999px !important;
    padding: 0.55rem 1.1rem !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    border-width: 1px !important;
    transition: 0.15s ease !important;
}

/* ============ PRIMARY ============ */
/* 主色：浅蓝背景 + 深灰文字 */
button[kind="primary"],
.stButton > button[kind="primary"] {
    background-color: #e0f2fe !important;
    border-color: #e0f2fe !important;
    color: #1f2937 !important;
    box-shadow: 
        0 4px 6px -1px rgba(0, 0, 0, 0.1),
        0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
}

button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover {
    background-color: #cce9fd !important;
    border-color: #cce9fd !important;
    color: #0f172a !important;
}

/* ============ SECONDARY ============ */
/* 次色：白底边框 + 暗灰文字 */
button[kind="secondary"],
.stButton > button[kind="secondary"] {
    background-color: #ffffff !important;
    border-color: #e5e7eb !important;
    color: #374151 !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05) !important;
}

button[kind="secondary"]:hover,
.stButton > button[kind="secondary"]:hover {
    background-color: #f3f4f6 !important;
    border-color: #e5e7eb !important;
    color: #111827 !important;
}

/*=============== STEP ================*/
.section-title {
    font-size: 18px;
    font-weight: bold;
    color: #1f1f1f;
    margin-bottom: 20px;
}

    
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# CONSTANTS - 自动从 data 目录加载 phase / document
# ============================================================================
@st.cache_data
def scan_data_structure():
    """
    扫描 data 目录下的所有 phase / document json 文件，返回结构：
    {
        "Design": {
            "folder": "design",
            "docs": {
                "Product Design": "CDC_UP_Product_Design_embedding.json",
                ...
            }
        },
        ...
    }
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")

    phase_map: dict[str, dict] = {}

    if not os.path.isdir(data_dir):
        return phase_map

    for phase_folder in os.listdir(data_dir):
        phase_path = os.path.join(data_dir, phase_folder)
        if not os.path.isdir(phase_path):
            continue

        # 展示给用户看的 phase 名（首字母大写）
        phase_display = phase_folder.capitalize()

        docs: dict[str, str] = {}
        for filename in os.listdir(phase_path):
            if not filename.endswith(".json"):
                continue

            # 根据文件名生成 document 展示名
            doc_name = os.path.splitext(filename)[0]  # 去掉 .json
            doc_name = doc_name.replace("_embedding", "")
            doc_name = doc_name.replace("CDC_UP_", "").replace("EPLC_", "")
            doc_name = doc_name.replace("_", " ")
            doc_name = doc_name.title()

            docs[doc_name] = filename

        if docs:
            phase_map[phase_display] = {
                "folder": phase_folder,
                "docs": docs,
            }

    return phase_map


PHASE_DOC_MAP = scan_data_structure()
PHASES = list(PHASE_DOC_MAP.keys())

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "learn_how"

if "current_question" not in st.session_state:
    st.session_state.current_question = ""

if "current_answer" not in st.session_state:
    st.session_state.current_answer = ""

# 问答历史列表，每个元素是一个字典 {"question": "...", "answer": "..."}
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

if "create_doc_step" not in st.session_state:
    st.session_state.create_doc_step = 1

if "selected_phase" not in st.session_state:
    st.session_state.selected_phase = None

if "selected_document" not in st.session_state:
    st.session_state.selected_document = None

if "generated_draft" not in st.session_state:
    st.session_state.generated_draft = ""

if "section_name" not in st.session_state:
    st.session_state.section_name = ""

if "user_details" not in st.session_state:
    st.session_state.user_details = ""

if "selected_section" not in st.session_state:
    st.session_state.selected_section = None

if "document_sections" not in st.session_state:
    st.session_state.document_sections = []

if "section_prompt_text" not in st.session_state:
    st.session_state.section_prompt_text = ""

# 儲存每個 section 的最新生成內容（key = section number）
if "section_generated_content" not in st.session_state:
    st.session_state.section_generated_content = {}

if "entered_content_page" not in st.session_state:
    st.session_state.entered_content_page = False

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================
@st.cache_data
def load_document_sections(phase: str, document: str):
    """
    根据 phase + document 名，从 data 目录加载对应 json 里的 sections
    """
    try:
        phase_info = PHASE_DOC_MAP.get(phase)
        if not phase_info:
            return []

        phase_folder = phase_info["folder"]
        filename = phase_info["docs"].get(document)
        if not filename:
            return []

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "data", phase_folder, filename)

        if not os.path.exists(file_path):
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sections = []
        for item in data:
            sections.append(
                {
                    "section_number": item.get("section_number", ""),
                    "section_title": item.get("section_title", ""),
                    "text": item.get("text", ""),
                }
            )

        # 排序逻辑
        def sort_key(section):
            num = section["section_number"]
            parts = num.split(".")
            key = []
            for part in parts:
                try:
                    key.append((0, int(part)))
                except ValueError:
                    key.append((1, part))
            return key

        try:
            sections.sort(key=sort_key)
        except Exception:
            sections.sort(key=lambda s: s["section_number"])

        return sections

    except Exception as e:
        st.error(f"Error loading sections: {str(e)}")
        return []

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
def show_sidebar():
    """Display sidebar with navigation"""
    with st.sidebar:
        st.markdown('<div class="sidebar-header">EPLC Assistant</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-subheader">Empowering IT Project Managers with<br>smarter, faster documentation.</div>',
            unsafe_allow_html=True,
        )




        if st.button(
            "💡 Learn How to Use",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "learn_how" else "secondary",
        ):
            st.session_state.current_page = "learn_how"
            st.rerun()

        if st.button(
            "💬 Ask a Question",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "ask_question" else "secondary",
        ):
            st.session_state.current_page = "ask_question"
            st.rerun()

        if st.button(
            "📄 Create EPLC Document",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "create_document" else "secondary",
        ):
            st.session_state.current_page = "create_document"
            st.session_state.create_doc_step = 1
            st.rerun()
            
        st.markdown("---")
        st.markdown(
            """
            <div style=' text-align: center;color:#9ca3af; font-size:0.9rem; line-height:1.4;'>
                Need raw templates?<br>
                <a href="https://web.archive.org/web/20240609100355/https:/www2.cdc.gov/cdcup/library/templates/default.htm#sthash.UcHHkg85.cHHkg856.dpbs" style="color:#3b82f6; text-decoration:none;">
                    Browse the EPLC Library
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )


  



# ============================================================================
# LEARN HOW TO USE PAGE
# ============================================================================

def show_learn_page():
    """How to Use 页面，带 Step 卡片 + Tips（文案按截图更新）"""

    # 顶部标题
    st.markdown('<div class="main-header">💡 How to Use EPLC Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">The EPLC Assistant helps IT project managers quickly understand EPLC phases and generate high-quality lifecycle documentation with smart automation.</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2, gap="large")

    # ================= 左侧：Ask a Question =================
    with col1:
        st.markdown(
            """
            <div class="feature-card">
              <div class="card-header-bg">
                <div class="card-title">
                    <span>💬</span> Ask a Question
                </div>
              </div>
              <div class="card-body">
                <div class="step-item">
                    <div class="step-icon">1</div>
                    <div class="step-content">
                        <h4>Ask your question</h4>
                        <p>Type any EPLC-related question (phase, template, policy, deliverables, etc.) in the input box.</p>
                    </div>
                </div>
                <div class="step-item">
                    <div class="step-icon">2</div>
                    <div class="step-content">
                        <h4> Get responses</h4>
                        <p>The assistant searches policy libraries and guidance, then returns a concise, EPLC-aligned answer.</p>
                    </div>
                </div>
                <div class="step-item">
                    <div class="step-icon">3</div>
                    <div class="step-content">
                        <h4> Review and reuse</h4>
                        <p>Copy, refine, or export the answer into your project documents or emails.</p>
                    </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

 
        st.markdown('<div class="bottom-cta">', unsafe_allow_html=True)
        if st.button("Go to Ask a Question 👉", key="btn_learn_ask", use_container_width=True, type="primary"):
            st.session_state.current_page = "ask_question"
            st.rerun()

    # ================= 右侧：Create a Document =================
    with col2:
        st.markdown(
            """
            <div class="feature-card">
              <div class="card-header-bg">
                <div class="card-title">
                    <span>📄</span> Create a Document
                </div>
              </div>
              <div class="card-body">
                <div class="step-item">
                    <div class="step-icon">1</div>
                    <div class="step-content">
                        <h4> Choose your phase</h4>
                        <p>Select the EPLC phase your project is in (e.g., Initiation, Design, Development, Implementation).</p>
                    </div>
                </div>
                <div class="step-item">
                    <div class="step-icon">2</div>
                    <div class="step-content">
                        <h4> Select a template</h4>
                        <p>Pick the document you need, such as Product Design, Test Plan, or Implementation Plan.</p>
                    </div>
                </div>
                <div class="step-item">
                    <div class="step-icon">3</div>
                    <div class="step-content">
                        <h4> Generate section by section</h4>
                        <p>Follow the section list, add your project context, and let the assistant draft each section for you.</p>
                    </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="bottom-cta">', unsafe_allow_html=True)
        if st.button("Go to Create a Document 👉", key="btn_learn_create", use_container_width=True, type="primary"):
            st.session_state.current_page = "create_document"
            st.session_state.create_doc_step = 1
            st.rerun()



# ============================================================================
# ASK A QUESTION PAGE
# ============================================================================
def show_ask_question_page():
    """Display Q&A page with Streamlit-assistant-like UI."""
    
    backend = get_backend()

    # =========================
    # 顶部：标题 + Restart 按钮
    # =========================
    title_col, restart_col = st.columns([8, 1])

    with title_col:
        # 标题始终存在
        st.markdown('<div class="main-header">💬 Ask a Question</div>', unsafe_allow_html=True)
    
    if st.session_state.qa_history:
        with restart_col:
            # 小空行，把按钮垂直挤到标题下缘附近
            st.write("")
            if st.button("Restart", key="restart_btn", use_container_width=True,):
                # 清空所有问答状态
                st.session_state.qa_history = []
                st.session_state.current_question = ""
                st.session_state.current_answer = ""
                # 如果你以后加了更多状态，也可以在这里顺便清
                st.rerun()

    # =========================
    # 状态一：还没有任何对话历史
    # =========================
    if not st.session_state.qa_history:

        first_question = st.chat_input("Ask a question...", key="first_question")

        st.markdown("<br>", unsafe_allow_html=True)

        suggestions = [
            "What is the EPLC Initial Phase?",
            "Show me a CDC UP template for planning.",
            "Explain the difference between initiation and planning phases.",
        ]

        sugg_cols = st.columns(len(suggestions))

        for idx, s in enumerate(suggestions):
            with sugg_cols[idx]:
                if st.button(s, key=f"suggestion_{idx}", use_container_width=True):
                    if not backend:
                        st.error("❌ Backend not available. Please check your configuration.")
                    else:
                        with st.spinner("🤔 Thinking..."):
                            result = backend.answer_question(s)

                        if result["success"]:
                            st.session_state.qa_history.append(
                                {"question": s, "answer": result["answer"]}
                            )
                        else:
                            st.session_state.qa_history.append(
                                {"question": s, "answer": f"❌ Error: {result['error']}"}
                            )
                    st.rerun()

        # 处理用户在 chat_input 里输入的第一个问题
        if first_question:
            if not backend:
                st.error("❌ Backend not available. Please check your configuration.")
            else:
                with st.spinner("🤔 Thinking..."):
                    result = backend.answer_question(first_question)

                if result["success"]:
                    st.session_state.qa_history.append(
                        {"question": first_question, "answer": result["answer"]}
                    )
                else:
                    st.session_state.qa_history.append(
                        {"question": first_question, "answer": f"❌ Error: {result['error']}"}
                    )
            st.rerun()

        # 初始态直接 return，不去渲染下面的 follow-up 区域
        return

    # =========================
    # 状态二：已有对话历史
    # =========================

    # 显示历史 QA
    for qa in st.session_state.qa_history:
        with st.chat_message("user"):
            st.write(qa["question"])
        with st.chat_message("assistant"):
            st.write(qa["answer"])

    # 底部 follow-up 输入框（唯一的 chat_input）
    follow_up = st.chat_input("Ask a follow-up...", key="followup_question")

    if follow_up:
        if not backend:
            st.error("❌ Backend not available. Please check your configuration.")
            st.session_state.qa_history.append(
                {
                    "question": follow_up,
                    "answer": "❌ Backend not available. Please check your configuration.",
                }
            )
        else:
            with st.spinner("🤔 Thinking..."):
                result = backend.answer_question(follow_up)

            if result["success"]:
                st.session_state.qa_history.append(
                    {"question": follow_up, "answer": result["answer"]}
                )
                st.session_state.current_question = follow_up
                st.session_state.current_answer = result["answer"]
            else:
                st.session_state.qa_history.append(
                    {"question": follow_up, "answer": f"❌ Error: {result['error']}"}
                )

        st.rerun()



# ============================================================================
# CREATE DOCUMENT - STEP 1: SELECT PHASE（选完之后才显示 STEP 2 和对应 Document）
# ============================================================================
def show_create_doc_step1():
    """Step 1: 先选 Phase，选完之后才显示 STEP 2 和对应 Document，并在右下角控制 Start writing"""

    # 顶部标题 + 说明
    st.markdown('<div class="main-header">📄 Create the EPLC Document</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Select your project phase to see available document templates.</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-title">STEP 1: Select a Phase</div>', unsafe_allow_html=True)

    if not PHASES:
        st.warning("No phases found in data folder.")
        return

    # ========== STEP 1：Phase 按钮 ==========
    cols = st.columns(min(4, len(PHASES)))
    for i, phase in enumerate(PHASES):
        with cols[i % len(cols)]:
            if st.button(
                phase,
                use_container_width=True,
                type="primary" if st.session_state.selected_phase == phase else "secondary",
                key=f"phase_{phase}",
            ):
                # 更新选中的 phase，同时清空之前选过的 document
                st.session_state.selected_phase = phase
                st.session_state.selected_document = None
                st.session_state.document_sections = []
                st.rerun()

    # ========== 只有在选了 Phase 之后，才显示 STEP 2 ==========
    if not st.session_state.selected_phase:
        # 还没选 phase，就先不画 STEP 2，也不画 Start writing（除了下面那一块）
        # 但我们还是让底部按钮显示，只是 disabled（下面 ready 会处理）
        # 所以这里直接往下走，不 return
        pass
    else:
        # 选完 Phase 后，再画 STEP 2 + Document 列表
        st.markdown('<div class="section-title">STEP 2: Select a Document</div>', unsafe_allow_html=True)

        phase_info = PHASE_DOC_MAP.get(st.session_state.selected_phase, {})
        doc_names = list(phase_info.get("docs", {}).keys())

        if not doc_names:
            st.warning("No documents found for this phase in data folder.")
        else:
            cols = st.columns(min(5, len(doc_names)))
            for i, doc in enumerate(doc_names):
                with cols[i % len(cols)]:
                    if st.button(
                        doc,
                        use_container_width=True,
                        type="primary" if st.session_state.selected_document == doc else "secondary",
                        key=f"doc_{doc}",
                    ):
                        # 这里只记录选中的 document，不直接跳到 step 3
                        st.session_state.selected_document = doc
                        # 可以预先加载 sections，后面 start writing 用
                        st.session_state.document_sections = load_document_sections(
                            st.session_state.selected_phase, doc
                        )
                        st.rerun()

    # ========== 页面底部右下角：Start writing 按钮 ==========
    st.markdown("<br><br>", unsafe_allow_html=True)
    spacer_col, btn_col = st.columns([5, 1])

    # 只有 phase + document 都选了才算 ready
    ready = bool(st.session_state.selected_phase and st.session_state.selected_document)

    with btn_col:
        if st.button(
            "Select Section →",
            key="start_writing_btn",
            use_container_width=True,
            type="primary" if ready else "secondary",
            disabled=not ready,  # 没选好就灰掉不能点
        ):
            # 双保险：如果还没加载 sections，这里再加载一次
            if not st.session_state.document_sections:
                st.session_state.document_sections = load_document_sections(
                    st.session_state.selected_phase,
                    st.session_state.selected_document,
                )
            st.session_state.create_doc_step = 3
            st.rerun()



# ============================================================================
# CREATE DOCUMENT - STEP 3: GENERATE CONTENT
# ============================================================================
def show_create_doc_step3():
    """Display document generation step with left-right layout"""
    backend = get_backend()
    
    # 确保 section 列表已经加载
    if not st.session_state.document_sections:
        st.session_state.document_sections = load_document_sections(
            st.session_state.selected_phase, st.session_state.selected_document
        )
    
    # 顶部：返回 + 当前 Phase / Document 信息
    header_col_left, header_col_right = st.columns([1, 18])
    with header_col_left:
        if st.button("←", key="back_to_doc_top"):
            # 回到 Step 1（重新选 Phase / Document）
            st.session_state.create_doc_step = 1
            st.session_state.selected_section = None
            st.session_state.section_prompt_text = ""
            st.session_state.entered_content_page = False
            st.rerun()
    with header_col_right:
        st.markdown(
            f"""
            <div style="font-size:20px; font-weight:700; ">
                {st.session_state.selected_document}
            </div>
            <div style="font-size:13px; text-transform:uppercase; letter-spacing:0.08em; color:#6b7280;">
                {st.session_state.selected_phase} Phase
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown("<hr style='margin-top:8px; margin-bottom:12px;'>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 2])

    # 左边：Section 列表
    

    with col_left:
        sections = st.session_state.document_sections

        if not sections:
            st.warning("No sections found for this document.")
        else:
            st.markdown('<div class="section-title">👇STEP 3: Select a Section</div>', unsafe_allow_html=True)

            options = []
            for s in sections:
                num = s["section_number"]
                title = s["section_title"]
                level = len(num.split(".")) - 1  # 0 顶层, 1 二级, 2+ 三级+
                if level == 0:
                    display = f"{num} {title}"
                elif level == 1:
                    display = f"   ▸ {num} {title}"
                else:
                    display = f"      • {num} {title}"
                options.append(display)

            if (
                st.session_state.selected_section is not None
                and st.session_state.selected_section < len(options)
            ):
                current_idx = st.session_state.selected_section
            else:
                current_idx = 0

            selected_label = st.radio(
                "section_list",
                options,
                index=current_idx,
                label_visibility="collapsed",
                key="section_radio_list"
            )

            st.session_state.selected_section = options.index(selected_label)


    # 右边：内容生成区
    with col_right:

        # --------- AFTER READY → SHOW REAL CONTENT GENERATION ---------

        selected_section_data = st.session_state.document_sections[
            st.session_state.selected_section
        ]

            
            
        # ----------------- WHAT TO WRITE 提示卡片（How To Use 风格） -----------------
        prompt_text = selected_section_data["text"]

        # Case 0: Empty text → Level-1 title, no content needed
        if prompt_text.strip() == "":
            st.markdown(
                '''
                <div style="color: #1f2937; margin-bottom: 6px; font-weight: 600;">
                    📌 This is a level-1 title
                </div>
                ''',
                unsafe_allow_html=True
            )
            st.info(
                "This is a level-1 title and does not require any content. "
                "Please select one of the sub-titles below and write content in that section."
            )
        elif "[" in prompt_text and "]" in prompt_text:
            prompt_start = prompt_text.find("[")
            prompt_end = prompt_text.find("]")

            if prompt_start < prompt_end:
                prompt = prompt_text[prompt_start + 1 : prompt_end]
                st.markdown(
                    f'''
                    <div style=" color: #1f2937; margin-bottom: 6px;">
                            🧠 What to write for this section：
                    </div>
                    ''',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"""
                    <div style="
                        background: #ffffff;
                        border: 1px solid #e5e7eb;
                        border-radius: 12px;
                        padding: 20px;
                        margin-bottom: 20px;
                    "
                        <div style=" color: #4b5563; line-height: 1.5;">
                            {prompt}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:
                st.info(f"💡 {prompt_text[:300]}...")

        else:
            st.markdown(
                    f'''
                    <div style=" color: #1f2937; margin-bottom: 6px;">
                            📋 Example content for this section：
                    </div>
                    ''',
                    unsafe_allow_html=True
                )
            st.markdown(
                    f"""
                    <div style="
                        background: #ffffff;
                        border: 1px solid #e5e7eb;
                        border-radius: 12px;
                        padding: 20px;
                        margin-bottom: 20px;
                    "
                        <div style=" color: #4b5563; line-height: 1.5;">
                            {prompt_text}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


        user_details = st.text_area(
            "✍ Describe your product/context:",
            value=st.session_state.user_details,
            height=150,
            key="details_input",
            placeholder="Provide details about your project, product, or specific requirements...",
        )

        instructions = st.text_area(
            "🚨 Additional Instructions (Optional):",
            height=100,
            key="instructions_input",
            placeholder="Any extra instructions for content generation...",
        )

        # 当前 section 的 key（比如 "1.2"）
        section_key = selected_section_data["section_number"]

        # 1️⃣ 按钮：负责“生成并存到 session_state”就完了
        if st.button("🚀 Generate Section", use_container_width=True, type="primary", key="generate_btn"):
            if not user_details:
                st.warning("⚠️ Please provide product/context details.")
            elif not backend:
                st.error("❌ Backend not available. Please check your configuration.")
            else:
                with st.spinner("🔄 Generating document section..."):
                    result = backend.generate_document_section(
                        phase=st.session_state.selected_phase,
                        template=st.session_state.selected_document,
                        section=selected_section_data["section_title"],
                        details=user_details,
                        instructions=instructions,
                    )

                if result["success"]:
                    # 把结果写进 session_state
                    st.session_state.generated_draft = result["draft"]
                    st.session_state.user_details = user_details
                    st.session_state.section_generated_content[section_key] = result["draft"]
                    st.success("✅ Section generated successfully!")
                else:
                    st.error(f"❌ Error: {result['error']}")

        # 2️⃣ 不管有没有刚点击按钮，每一轮都来这里读 & 展示
        section_output = st.session_state.section_generated_content.get(section_key, "")

        if section_output:
            st.markdown("---")
            st.markdown("#### 📄 Generated Content")
            st.markdown(section_output)

            st.markdown("<br>", unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])

            with col1:
                st.download_button(
                    label="📥 Download Section as a Text File",
                    data=section_output,
                    file_name=f"{st.session_state.selected_document}_{section_key}_{selected_section_data['section_title']}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="download_btn_visible",
                )

            with col2:
                regen_clicked = st.button(
                    "🔄 Regenerate",
                    use_container_width=True,
                    key="regenerate_btn_visible"
                )
                if regen_clicked:
                    if backend:
                        with st.spinner("🔄 Regenerating..."):
                            result = backend.generate_document_section(
                                phase=st.session_state.selected_phase,
                                template=st.session_state.selected_document,
                                section=selected_section_data["section_title"],
                                details=st.session_state.user_details,
                                instructions="",  # 这里你也可以继续用 instructions
                            )
                        if result["success"]:
                            st.session_state.generated_draft = result["draft"]
                            st.session_state.section_generated_content[section_key] = result["draft"]
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {result['error']}")


# ============================================================================
# CREATE DOCUMENT MAIN PAGE
# ============================================================================

def show_create_document_page():
    """Display appropriate step in document creation workflow"""

    # 现在只保留两个步骤：
    # step 1: 选 phase + document（同一页）
    # step 3: 生成内容
    if st.session_state.create_doc_step == 1:
        show_create_doc_step1()
    elif st.session_state.create_doc_step == 3:
        show_create_doc_step3()


# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    """Main application entry point"""

    st.markdown(
        """
        <style>
        .top-right-github-btn {
            position: fixed;
            top: 12px;
            right: 16px;
            z-index: 9999;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 9999px;
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            box-shadow: 0 2px 4px rgba(15, 23, 42, 0.08);
            font-size: 13px;
            font-weight: 500;
            color: #111827;
            text-decoration: none;
            transition: all 0.2s ease;
        }
        
        .top-right-github-btn:hover {
            background-color: #f3f4f6;
            border-color: #d1d5db;
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(15, 23, 42, 0.12);
        }
        
        .top-right-github-btn svg {
            width: 16px;
            height: 16px;
            flex-shrink: 0;
        }
        </style>
        
        <a class="top-right-github-btn"
           href="https://github.com/XinleiCheng/QMSS_IBM_Practicum_2025Fall"
           target="_blank">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 30">
                <path fill="#111827" d="M15,3C8.373,3,3,8.373,3,15c0,5.623,3.872,10.328,9.092,11.63C12.036,26.468,12,26.28,12,26.047v-2.051 c-0.487,0-1.303,0-1.508,0c-0.821,0-1.551-0.353-1.905-1.009c-0.393-0.729-0.461-1.844-1.435-2.526 c-0.289-0.227-0.069-0.486,0.264-0.451c0.615,0.174,1.125,0.596,1.605,1.222c0.478,0.627,0.703,0.769,1.596,0.769 c0.433,0,1.081-0.025,1.691-0.121c0.328-0.833,0.895-1.6,1.588-1.962c-3.996-0.411-5.903-2.399-5.903-5.098 c0-1.162,0.495-2.286,1.336-3.233C9.053,10.647,8.706,8.73,9.435,8c1.798,0,2.885,1.166,3.146,1.481C13.477,9.174,14.461,9,15.495,9 c1.036,0,2.024,0.174,2.922,0.483C18.675,9.17,19.763,8,21.565,8c0.732,0.731,0.381,2.656,0.102,3.594 c0.836,0.945,1.328,2.066,1.328,3.226c0,2.697-1.904,4.684-5.894,5.097C18.199,20.49,19,22.1,19,23.313v2.734 c0,0.104-0.023,0.179-0.035,0.268C23.641,24.676,27,20.236,27,15C27,8.373,21.627,3,15,3z"></path>
            </svg>
            <span>GitHub</span>
        </a>
        """,
        unsafe_allow_html=True,
    )
    show_sidebar()

    if st.session_state.current_page == "learn_how":
        show_learn_page()
    elif st.session_state.current_page == "ask_question":
        show_ask_question_page()
    elif st.session_state.current_page == "create_document":
        show_create_document_page()


if __name__ == "__main__":
    main()
