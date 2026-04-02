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

def load_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    chunks = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            # Har page ko 1000 character ke chunks mein todo
            for j in range(0, len(text), 1000):
                chunks.append({
                    "text": text[j:j+1000],
                    "id": f"page{i}_chunk{j}"
                })
    return chunks

def create_vectorstore(chunks):
    try:
        chroma_client.delete_collection("documents")
    except:
        pass
    
    collection = chroma_client.create_collection(
        name="documents",
        embedding_function=embed_fn
    )
    
    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    collection.add(documents=texts, ids=ids)
    return collection

def load_vectorstore():
    return chroma_client.get_collection(
        name="documents",
        embedding_function=embed_fn
    )

def get_answer(collection, question):
    results = collection.query(query_texts=[question], n_results=3)
    context = "\n\n".join(results["documents"][0])
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Neeche diye context ke basis pe sawaal ka jawab do. Agar jawab nahi pata toh 'Mujhe nahi pata' bolo."
            },
            {
                "role": "user", 
                "content": f"Context:\n{context}\n\nSawaal: {question}"
            }
        ]
    )
    
    return {
        "answer": response.choices[0].message.content,
        "sources": results["documents"][0]
    }