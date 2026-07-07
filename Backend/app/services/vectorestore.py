# backend/app/services/vectorestore.py
import os
import shutil
import warnings
import base64

warnings.filterwarnings("ignore", category=DeprecationWarning)

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage

from app.config import EMBEDDING_MODEL, UPLOAD_DIR, DB_DIR, CHUNK_SIZE, CHUNK_OVERLAP

embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

# ==========================================
# NEW: Vision Processing Utilities
# ==========================================
def encode_image(image_path):
    """Converts an image file to a base64 string for the VLM."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def process_image_with_vision(file_path):
    """Passes the image to Ollama's Vision model and returns a descriptive Document."""
    filename = os.path.basename(file_path)
    print(f"  -> Analyzing image: {filename} with Vision Model...")
    
    base64_image = encode_image(file_path)
    
    
    vision_llm = ChatOllama(model="llava", temperature=0)
    
    # Create the multimodal prompt
    message = HumanMessage(
        content=[
            {
                "type": "text", 
                "text": "You are an expert analyst. Describe this image, chart, or diagram in extreme detail. Explain the relationships between elements, read all visible text, and summarize the core meaning so someone who cannot see the image would understand it perfectly."
            },
            {
                "type": "image_url", 
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            }
        ]
    )
    
    # Generate the description
    response = vision_llm.invoke([message])
    
    # Wrap it in a Langchain Document so FAISS can index it
    return Document(
        page_content=f"[IMAGE CONTEXT: {filename}]\n{response.content}",
        metadata={"source": file_path, "type": "image_summary"}
    )

# ==========================================
# Main Ingestion Logic
# ==========================================
def build_vectordatabase():
    print(f"Scanning {UPLOAD_DIR} for documents and images...")
    
    if not os.path.exists(UPLOAD_DIR):
        msg = f"ERROR: The directory '{UPLOAD_DIR}' does not exist!"
        print(msg)
        return msg

    # 1. Standard Loaders for Text & PDFs
    # We turn OFF extract_images in PDFs so we don't accidentally send hundreds of tiny PDF icons to the heavy Vision model.
    text_loader = DirectoryLoader(UPLOAD_DIR, glob="**/*.txt", loader_cls=TextLoader)
    pdf_loader = DirectoryLoader(UPLOAD_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
    
    documents = text_loader.load() + pdf_loader.load()

    # 2. Custom Loader for Raw Images
    image_docs = []
    for filename in os.listdir(UPLOAD_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_path = os.path.join(UPLOAD_DIR, filename)
            try:
                img_doc = process_image_with_vision(file_path)
                image_docs.append(img_doc)
            except Exception as e:
                print(f"  -> Failed to process image {filename}: {e}")

    # Combine everything
    documents.extend(image_docs)

    if len(documents) == 0:
        msg = "ERROR: No compatible files found."
        print(msg)
        return msg

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    
    print(f"Splitting into chunks and generating embeddings...")
    chunks = text_splitter.split_documents(documents)
    
    vectordb = FAISS.from_documents(chunks, embeddings)
    vectordb.save_local(DB_DIR)
    
    success_msg = f"Success! Database created with {len(chunks)} chunks."
    print(success_msg)
    return success_msg

def clear_vectordatabase():
    """Deletes the vector database and uploaded files to start fresh."""
    try:
        if os.path.exists(DB_DIR):
            shutil.rmtree(DB_DIR)
            os.makedirs(DB_DIR)
        
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    
        return "Memory wiped. Ready for new documents!"
    except Exception as e:
        return f"Error clearing database: {str(e)}"

if __name__ == "__main__":
    build_vectordatabase()