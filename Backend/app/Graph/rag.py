# backend/app/graph/rag.py
import os
import builtins
import uuid
import base64  
builtins.uuid = uuid

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.tools.retriever import create_retriever_tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import Tool, tool  
from langchain_core.messages import HumanMessage  

from app.config import DB_DIR, EMBEDDING_MODEL

# ==========================================
# 1. Initialize Models
# ==========================================
# Main reasoning and tool-calling model
llm = ChatOllama(model="qwen2.5:3b", temperature=0)

# Multimodal vision model
vision_llm = ChatOllama(model="llama3.2-vision", temperature=0)

# Embeddings for the FAISS vector store
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)


# ==========================================
# 2. Define Custom Vision Tool
# ==========================================
@tool
def analyze_image_tool(image_path: str, prompt: str) -> str:
    """
    Use this tool ONLY when the user asks you to look at, read, or describe an image file.
    Provide the path to the image file, and a prompt asking what you want to know about it.
    """
    try:
        # Open the image and encode it to base64 so the local model can "see" it
        with open(image_path, "rb") as img_file:
            img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
        
        # Package the image and the question for Llama 3.2 Vision
        msg = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        )
        
        # Get the description from the vision model
        response = vision_llm.invoke([msg])
        return response.content
    except Exception as e:
        return f"Failed to analyze image at {image_path}. Error: {str(e)}"


# ==========================================
# 3. Define the Agent's Toolbelt
# ==========================================
tools = []

# Tool A: Live Web Search
web_search = DuckDuckGoSearchRun()
tools.append(
    Tool(
        name="web_search",
        description="Search the internet for current events, facts, or information not found in the local documents.",
        func=web_search.run,
    )
)

# Tool B: Multimodal Vision
tools.append(analyze_image_tool)

# Tool C: Local Document Retriever (Only loaded if a database exists)
if os.path.exists(DB_DIR) and os.listdir(DB_DIR):
    try:
        db = FAISS.load_local(DB_DIR, embeddings, allow_dangerous_deserialization=True)
        retriever = db.as_retriever(search_kwargs={"k": 3})
        
        retriever_tool = create_retriever_tool(
            retriever,
            "local_document_search",
            "Search and return information from the user's uploaded local text documents. Always try this first if the user asks about their files."
        )
        tools.append(retriever_tool)
    except Exception as e:
        print(f"Warning: Could not load retriever tool: {e}")


# ==========================================
# 4. Create the ReAct Agent Graph
# ==========================================
system_prompt = """You are a highly intelligent AI assistant. You have access to tools. 
If the user asks a general question, answer it directly. 
If the user asks about their documents, use the 'local_document_search' tool.
If the user asks about an image or picture, use the 'analyze_image_tool'.
If the answer is not in the documents, or the user asks about current events, use the 'web_search' tool.
Do not hallucinate. If you don't know, use a tool to find out."""

memory = MemorySaver()

# Boot up the multi-agent graph
app_graph = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=system_prompt,
    checkpointer=memory
)