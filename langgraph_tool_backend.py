# backend.py

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import sqlite3
from core.config import LLM_MODEL, DB_PATH
import tools.memory_tools as memory_tools
from tools.registry import ALL_TOOLS, build_llm_with_tools
import memory.service as memory_service


# LLM and tools are now managed by tools/registry.py
llm = ChatOpenAI(streaming=True, model=LLM_MODEL)
llm_with_tools = build_llm_with_tools()

# -------------------
# 3. State
# -------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# -------------------
# 4. Nodes
# -------------------
def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    
    memories = memory_service.get_all_memories()
    system_prompt = "You are a helpful AI assistant."
    if memories:
        system_prompt += (
            "\n\nCRITICAL OVERRIDE: The following facts represent the single source of truth about the user. "
            "If the user's past conversational history contradicts these facts, you must ALWAYS trust the facts below. "
            "If the user's new message updates or contradicts these facts, you MUST use the `update_memory` tool to replace the outdated fact ID with the new information. "
            "Never let two facts about the same subject coexist in memory.\n\n"
            f"{memories}"
        )
        
    messages_to_invoke = [SystemMessage(content=system_prompt)] + messages
    
    response = llm_with_tools.invoke(messages_to_invoke)
    return {"messages": [response]}

tool_node = ToolNode(ALL_TOOLS)

# -------------------
# 5. Checkpointer
# -------------------
conn = sqlite3.connect(database=DB_PATH, check_same_thread=False)
# Initialize metadata table
conn.execute("""
    CREATE TABLE IF NOT EXISTS thread_metadata (
        thread_id TEXT PRIMARY KEY,
        title TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Initialize user memory table
conn.execute("""
    CREATE TABLE IF NOT EXISTS user_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fact TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
# Migration: Add last_updated column if it doesn't exist (for existing DBs)
try:
    conn.execute("ALTER TABLE thread_metadata ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
except sqlite3.OperationalError:
    pass # Column likely already exists

# Backfill: Ensure all threads from checkpoints exist in metadata
conn.execute("""
    INSERT OR IGNORE INTO thread_metadata (thread_id, title, last_updated)
    SELECT DISTINCT thread_id, 'New Chat', CURRENT_TIMESTAMP FROM checkpoints
""")
conn.commit()

# Inject the database connection into memory service and tools
memory_service.set_connection(conn)
memory_tools.set_connection(conn)


checkpointer = SqliteSaver(conn=conn)

# -------------------
# 6. Graph
# -------------------
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")

graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer=checkpointer)

# -------------------
# 7. Helper
# -------------------

def save_thread_title(thread_id: str, title: str):
    try:
        # Update title and timestamp
        conn.execute("""
            INSERT INTO thread_metadata (thread_id, title, last_updated) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(thread_id) DO UPDATE SET 
                title=excluded.title, 
                last_updated=CURRENT_TIMESTAMP
        """, (thread_id, title))
        conn.commit()
    except Exception as e:
        print(f"Error saving title: {e}")

def update_thread_timestamp(thread_id: str):
    try:
        # Ensure thread exists in metadata and update timestamp
        conn.execute("""
            INSERT INTO thread_metadata (thread_id, title, last_updated) 
            VALUES (?, 'New Chat', CURRENT_TIMESTAMP)
            ON CONFLICT(thread_id) DO UPDATE SET 
                last_updated=CURRENT_TIMESTAMP
        """, (thread_id,))
        conn.commit()
    except Exception as e:
        print(f"Error updating timestamp: {e}")

def generate_title(message_content: str) -> str:
    try:
        # Use a lightweight invocation to get a title
        prompt = f"Summarize this message into a concise 3-5 word title. Do not use quotes. Message: {message_content}"
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"Error generating title: {e}")
        return "New Conversation"

def retrieve_all_threads():
    # Get threads from metadata, ordered by last_updated DESC
    cursor = conn.execute("SELECT thread_id, title FROM thread_metadata ORDER BY last_updated DESC")
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row[0],
            "title": row[1]
        })
    return results

def delete_thread(thread_id: str):
    try:
        conn.execute("DELETE FROM thread_metadata WHERE thread_id = ?", (thread_id,))
        conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting thread: {e}")
        return False