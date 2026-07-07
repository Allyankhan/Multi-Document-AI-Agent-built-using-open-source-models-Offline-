# backend/app/main.py
from pydantic import BaseModel
from app.Graph.rag import app_graph
import os
import shutil
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.vectorestore import build_vectordatabase, clear_vectordatabase

# Import the ingestion function and config variables directly
from app.services.vectorestore import build_vectordatabase
from app.config import UPLOAD_DIR 

app = FastAPI(title="Local Multi-Doc AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the upload directory exists at startup
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "llama3 via Ollama"}

@app.post("/upload")
async def upload_documents(files: List[UploadFile]):
    """
    Endpoint to upload multiple documents, save them locally, 
    and trigger the vector store ingestion.
    """
    saved_files = []
    
    for file in files:
     if not file.filename.lower().endswith(('.pdf', '.txt', '.png', '.jpg', '.jpeg')):
       raise HTTPException(
        status_code=400, 
        detail=f"Unsupported file type: {file.filename}. Allowed: PDF, TXT, PNG, JPG."
    )
            
        
       
    file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # Save the file to disk asynchronously
    try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file.filename)
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not save file {file.filename}: {str(e)}")
    finally:
            file.file.close()

    # Trigger the ingestion process now that files are saved
    try:
        # This will now capture the success/error string from vectorestore.py
        ingestion_result = build_vectordatabase() 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    return {
        "message": "Files uploaded and processed successfully",
        "uploaded_files": saved_files,
        "ingestion_status": ingestion_result
    }
class ChatRequest(BaseModel):
    question: str

# backend/app/main.py (Scroll to the bottom)

class ChatRequest(BaseModel):
    question: str
    session_id: str = "default_session"

@app.post("/chat")
async def chat_with_docs(request: ChatRequest):
    """
    Endpoint to trigger the Tool-Calling ReAct Agent.
    """
    try:
        # LangGraph agents expect an array of messages
        initial_state = {"messages": [("user", request.question)]}
        config = {"configurable": {"thread_id": request.session_id}}
        
        # Invoke the Agent
        result = app_graph.invoke(initial_state, config=config)
        
        # The agent returns a list of messages. The last one is the final AI response.
        final_message = result["messages"][-1].content
        
        return {"answer": final_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")