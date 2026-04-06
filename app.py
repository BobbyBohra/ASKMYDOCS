import streamlit as st
import os
import tempfile
from rag_engine import load_pdf, create_vectorstore, add_to_vectorstore, load_vectorstore, get_answer

st.set_page_config(
    page_title="AskMyDocs",
    page_icon="🤖",
    layout="wide"
)

# ✅ Real Premium CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500&family=Syne:wght@700;800&display=swap');

.stApp {
    background: #0a0a0f !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stApp::before {
    content: '';
    position: fixed;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(124,58,237,0.15), transparent 70%);
    top: -100px; left: -100px;
    pointer-events: none;
    z-index: 0;
}
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.03) !important;
    border-right: 0.5px solid rgba(255,255,255,0.08) !important;
}
h1 {
    font-family: 'Syne', sans-serif !important;
    background: linear-gradient(90deg, #e8e6f0, #a78bfa) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
}
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.03) !important;
    border: 0.5px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
    color: #e8e6f0 !important;
}
[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.04) !important;
    border: 0.5px solid rgba(124,58,237,0.3) !important;
    border-radius: 14px !important;
    color: #e8e6f0 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
}
[data-testid="stFileUploader"] {
    background: rgba(124,58,237,0.05) !important;
    border: 1px dashed rgba(124,58,237,0.4) !important;
    border-radius: 12px !important;
}
p, label, .stMarkdown {
    color: rgba(255,255,255,0.7) !important;
}
.stSuccess {
    background: rgba(16,185,129,0.08) !important;
    border: 0.5px solid rgba(16,185,129,0.2) !important;
    border-radius: 10px !important;
}
.stWarning {
    background: rgba(245,158,11,0.08) !important;
    border: 0.5px solid rgba(245,158,11,0.2) !important;
    border-radius: 10px !important;
}
.stError {
    background: rgba(239,68,68,0.08) !important;
    border: 0.5px solid rgba(239,68,68,0.2) !important;
    border-radius: 10px !important;
}
.stSpinner { color: #a78bfa !important; }
div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 0.5px solid rgba(255,255,255,0.06) !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 AskMyDocs — PDF se Baat Karo!")
st.markdown("Multiple PDFs upload karo aur koi bhi sawaal poochho!")

# ✅ Session State
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0
if "uploaded_pdfs" not in st.session_state:
    st.session_state.uploaded_pdfs = []

# ✅ Sidebar
with st.sidebar:
    st.header("📄 PDF Upload")

    uploaded_files = st.file_uploader(
        "PDF files choose karo",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files:
        new_files = [
            f for f in uploaded_files
            if f.name not in st.session_state.uploaded_pdfs
        ]

        if new_files:
            if st.button("🚀 Process PDFs", type="primary"):
                all_chunks = []

                for uploaded_file in new_files:
                    with st.spinner(f"Processing: {uploaded_file.name}..."):
                        try:
                            with tempfile.NamedTemporaryFile(
                                delete=False,
                                suffix=".pdf"
                            ) as tmp:
                                tmp.write(uploaded_file.read())
                                tmp_path = tmp.name

                            chunks = load_pdf(
                                tmp_path,
                                pdf_name=uploaded_file.name
                            )

                            if len(chunks) == 0:
                                st.warning(f"⚠️ {uploaded_file.name} se text nahi nikla!")
                            else:
                                all_chunks.extend(chunks)
                                st.session_state.uploaded_pdfs.append(
                                    uploaded_file.name
                                )
                                st.success(f"✅ {uploaded_file.name} — {len(chunks)} chunks")

                        except Exception as e:
                            st.error(f"❌ {uploaded_file.name}: {str(e)}")

                        finally:
                            if os.path.exists(tmp_path):
                                os.unlink(tmp_path)

                if all_chunks:
                    if not st.session_state.pdf_processed:
                        create_vectorstore(all_chunks)
                    else:
                        add_to_vectorstore(all_chunks)

                    st.session_state.chunk_count += len(all_chunks)
                    st.session_state.pdf_processed = True

    # ✅ Status Section
    st.divider()
    if st.session_state.pdf_processed:
        st.success("✅ PDF Ready!")
        st.info(f"📊 {st.session_state.chunk_count} chunks loaded")

        st.markdown("**📚 Loaded PDFs:**")
        for pdf in st.session_state.uploaded_pdfs:
            st.markdown(f"✅ `{pdf}`")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Chat Clear"):
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("♻️ Reset All"):
                st.session_state.pdf_processed = False
                st.session_state.messages = []
                st.session_state.uploaded_pdfs = []
                st.session_state.chunk_count = 0
                try:
                    import chromadb
                    c = chromadb.PersistentClient(path="./chroma_db")
                    c.delete_collection("documents")
                except:
                    pass
                st.rerun()
    else:
        st.warning("⚠️ Koi PDF load nahi hai")

# ✅ Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ✅ Chat Input
if prompt := st.chat_input("Sawaal poochho..."):
    if not st.session_state.pdf_processed:
        st.error("⚠️ Pehle PDF upload aur process karo!")
    else:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Soch raha hoon... 🤔"):
                try:
                    collection = load_vectorstore()
                    result = get_answer(collection, prompt)

                    st.write(result["answer"])

                    if result.get("pdf_sources"):
                        st.caption(
                            f"📄 Source PDFs: {', '.join(result['pdf_sources'])}"
                        )

                    with st.expander("📚 Sources dekho"):
                        for i, source in enumerate(result["sources"]):
                            st.markdown(f"**Source {i+1}:**")
                            st.caption(source[:300] + "...")
                            st.divider()

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"]
                    })

                except Exception as e:
                    st.error("❌ Kuch gadbad hui! Dobara try karo.")
                    st.caption(f"Error: {str(e)}")
