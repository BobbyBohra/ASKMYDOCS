import streamlit as st
import os
import tempfile
from rag_engine import load_pdf, create_vectorstore, load_vectorstore, get_answer

st.set_page_config(page_title="AskMyDocs", page_icon="🤖", layout="wide")

st.title("🤖 AskMyDocs — PDF se Baat Karo!")
st.markdown("Apna PDF upload karo aur koi bhi sawaal poochho!")

with st.sidebar:
    st.header("📄 PDF Upload")
    uploaded_file = st.file_uploader("PDF file choose karo", type="pdf")
    
    if uploaded_file:
        if st.button("🚀 Process PDF", type="primary"):
            with st.spinner("PDF process ho raha hai..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                chunks = load_pdf(tmp_path)
                create_vectorstore(chunks)
                os.unlink(tmp_path)
                st.session_state.pdf_processed = True
                st.success(f"✅ Done! {len(chunks)} chunks bane!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Sawaal poochho..."):
    if not os.path.exists("./chroma_db"):
        st.error("⚠️ Pehle PDF upload karo!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Soch raha hoon..."):
                collection = load_vectorstore()
                result = get_answer(collection, prompt)
                
                st.write(result["answer"])
                
                with st.expander("📚 Sources dekho"):
                    for i, source in enumerate(result["sources"]):
                        st.write(f"**Source {i+1}:** {source[:300]}...")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"]
                })