import os
import chromadb
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embed_fn = DefaultEmbeddingFunction()

def load_pdf(pdf_path, pdf_name="document"):  # ✅ pdf_name add kiya
    reader = PdfReader(pdf_path)
    full_text = ""
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            full_text += f"\n{text}"
    
    chunks = []
    chunk_size = 1000
    overlap = 200
    words = full_text.split()
    
    i = 0
    chunk_num = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        
        if chunk_text.strip():
            chunks.append({
                "text": chunk_text,
                # ✅ Har chunk ko PDF name se tag karo
                "id": f"{pdf_name}_chunk_{chunk_num}",
                "source": pdf_name
            })
        
        i += chunk_size - overlap
        chunk_num += 1
    
    return chunks

def create_vectorstore(all_chunks):
    # ✅ Purana data delete karo
    try:
        chroma_client.delete_collection("documents")
    except:
        pass
    
    collection = chroma_client.create_collection(
        name="documents",
        embedding_function=embed_fn
    )
    
    texts = [c["text"] for c in all_chunks]
    ids = [c["id"] for c in all_chunks]
    
    # ✅ Har chunk ke saath PDF name bhi store karo
    metadatas = [{"source": c["source"]} for c in all_chunks]
    
    collection.add(
        documents=texts,
        ids=ids,
        metadatas=metadatas  # ✅ Metadata add kiya
    )
    return collection

def add_to_vectorstore(new_chunks):
    # ✅ Naya function — existing DB mein add karo
    try:
        collection = chroma_client.get_collection(
            name="documents",
            embedding_function=embed_fn
        )
    except:
        collection = chroma_client.create_collection(
            name="documents",
            embedding_function=embed_fn
        )
    
    texts = [c["text"] for c in new_chunks]
    ids = [c["id"] for c in new_chunks]
    metadatas = [{"source": c["source"]} for c in new_chunks]
    
    collection.add(
        documents=texts,
        ids=ids,
        metadatas=metadatas
    )
    return collection

def load_vectorstore():
    return chroma_client.get_collection(
        name="documents",
        embedding_function=embed_fn
    )

def get_answer(collection, question):
    results = collection.query(
        query_texts=[question],
        n_results=5,
        include=["documents", "metadatas"]  # ✅ Source bhi lo
    )
    
    context = "\n\n".join(results["documents"][0])
    
    # ✅ Kaun se PDF se answer aaya — track karo
    sources = []
    for meta in results["metadatas"][0]:
        if meta["source"] not in sources:
            sources.append(meta["source"])
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """Tu ek helpful PDF assistant hai.
Tujhe multiple PDFs ka content diya gaya hai.
Tu SIRF us content ke basis pe jawab dega.
Agar multiple PDFs mein information ho toh combine karke batao.
Jawab Hindi ya English mein de."""
            },
            {
                "role": "user",
                "content": f"""PDF Content:
{context}

Sawaal: {question}"""
            }
        ],
        temperature=0.3,
        max_tokens=1024
    )
    
    return {
        "answer": response.choices[0].message.content,
        "sources": results["documents"][0],
        "pdf_sources": sources  # ✅ Kaun se PDF se answer aaya
    }
