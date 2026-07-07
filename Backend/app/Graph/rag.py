# backend/app/graph/rag.py
import os
import builtins
import uuid
builtins.uuid = uuid
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.tools.retriever import create_retriever_tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import Tool


from app.config import DB_DIR, EMBEDDING_MODEL

# ==========================================
# 1. Initialize Models
# ==========================================
# We use Qwen 2.5 because it has excellent native tool-calling capabilities!
llm = ChatOllama(model="qwen2.5:3b", temperature=0)
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

# ==========================================
# 2. Define the Agent's Tools
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

# Tool B: Local Document Retriever (Only loaded if a database exists)
if os.path.exists(DB_DIR) and os.listdir(DB_DIR):
    try:
        db = FAISS.load_local(DB_DIR, embeddings, allow_dangerous_deserialization=True)
        retriever = db.as_retriever(search_kwargs={"k": 3})
        
        # This magically turns our FAISS database into a callable tool!
        retriever_tool = create_retriever_tool(
            retriever,
            "local_document_search",
            "Search and return information from the user's uploaded local documents and images. Always try this first if the user asks about their files."
        )
        tools.append(retriever_tool)
    except Exception as e:
        print(f"Warning: Could not load retriever tool: {e}")

# ==========================================
# 3. Create the ReAct Agent Graph
# ==========================================
system_prompt = """You are a highly intelligent AI assistant. You have access to tools. 
If the user asks a general question, answer it. 
If the user asks about their documents, use the 'local_document_search' tool.
If the answer is not in the documents, or the user asks about current events, use the 'web_search' tool.
Do not hallucinate. If you don't know, use a tool to find out."""

memory = MemorySaver()

# LangGraph's prebuilt agent handles the loop of: Think -> Call Tool -> Read Result -> Answer
app_graph = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory
    
)