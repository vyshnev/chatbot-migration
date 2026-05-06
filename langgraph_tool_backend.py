# backend.py

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from datetime import datetime
import os
import hashlib
import json
from dotenv import load_dotenv
from upstash_redis import Redis
import sqlite3
import requests

# Load environment variables
load_dotenv()

# Initialize Upstash Redis client
try:
    redis_client = Redis.from_env()
except Exception as e:
    print(f"Warning: Could not initialize Upstash Redis client: {e}")
    redis_client = None

def execute_with_cache(tool_name: str, func, ttl_seconds: int, *args, **kwargs):
    """Executes a function with Redis caching."""
    if not redis_client:
        return func(*args, **kwargs)
        
    try:
        # Create a deterministic cache key based on tool name and arguments
        arg_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        key_hash = hashlib.md5(arg_str.encode()).hexdigest()
        cache_key = f"cache:{tool_name}:{key_hash}"
        
        # Check cache
        cached_result = redis_client.get(cache_key)
        if cached_result:
            print(f"[CACHE HIT] Returning cached result for {tool_name}")
            # upstash_redis usually parses json automatically, but let's be safe
            if isinstance(cached_result, str):
                try:
                    return json.loads(cached_result)
                except json.JSONDecodeError:
                    return cached_result
            return cached_result
            
        print(f"[CACHE MISS] Executing {tool_name}...")
        # Execute function
        result = func(*args, **kwargs)
        
        # Store in cache
        if isinstance(result, (dict, list)):
            redis_client.setex(cache_key, ttl_seconds, json.dumps(result))
        else:
            redis_client.setex(cache_key, ttl_seconds, str(result))
            
        return result
    except Exception as e:
        print(f"Cache Error ({tool_name}): {e}")
        return func(*args, **kwargs)

# -------------------
# 1. LLM
# -------------------
llm = ChatOpenAI(streaming=True, model="gpt-4o")

# -------------------
# 2. Tools
# -------------------
# Tools
_raw_search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def search_tool(query: str) -> str:
    """
    Search the web for information. Use this when you need up-to-date facts.
    """
    return execute_with_cache("search_tool", _raw_search_tool.invoke, 7200, query)

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}



@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=34MYR53FBF6HDXHN"
    
    def fetch_stock():
        r = requests.get(url)
        return r.json()
        
    return execute_with_cache("get_stock_price", fetch_stock, 300)



@tool
def save_memory(fact: str) -> str:
    """
    Save an important fact or preference about the user to long-term memory.
    CRITICAL WARNING: DO NOT use this tool if the user is changing or updating a fact you already know. You MUST use `update_memory` instead to prevent duplicates.
    CRITICAL: Always save ONE discrete, atomic piece of information per call. Do not save compound sentences. 
    If you need to save multiple facts, call this tool multiple times in parallel.
    """
    try:
        cursor = conn.execute("INSERT OR IGNORE INTO user_memory (fact) VALUES (?)", (fact,))
        conn.commit()
        if cursor.rowcount == 0:
            return "Already remembered."
        return "Fact remembered."
    except Exception as e:
        return f"Error saving memory: {e}"

@tool
def forget_memory(memory_id: int) -> str:
    """
    Delete a specific fact from long-term memory using its ID.
    Use this when the user asks you to forget something or when a fact is no longer true.
    """
    try:
        cursor = conn.execute("DELETE FROM user_memory WHERE id = ?", (memory_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return f"No memory found with ID {memory_id}."
        return "Memory forgotten."
    except Exception as e:
        return f"Error forgetting memory: {e}"

@tool
def update_memory(old_memory_id: int, new_fact: str) -> str:
    """
    Update an existing fact in long-term memory. 
    Use this when the user's new message updates or contradicts an existing memory.
    The `old_memory_id` MUST be the exact integer found inside the `[ID: X]` tag of the existing memory you are replacing.
    """
    try:
        cursor = conn.execute(
            "UPDATE user_memory SET fact = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_fact, old_memory_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return f"No memory found with ID {old_memory_id}."
        return "Memory updated successfully."
    except Exception as e:
        return f"Error updating memory: {e}"

tools = [search_tool, get_stock_price, calculator, save_memory, forget_memory, update_memory]
llm_with_tools = llm.bind_tools(tools)

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
    
    memories = get_user_memories()
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

tool_node = ToolNode(tools)

# -------------------
# 5. Checkpointer
# -------------------
conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
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
def get_user_memories() -> str:
    try:
        cursor = conn.execute("SELECT id, fact, date(created_at) FROM user_memory ORDER BY created_at ASC")
        facts = [f"- [ID: {row[0]}] {row[1]} (Saved: {row[2]})" for row in cursor.fetchall()]
        if facts:
            return "\n".join(facts)
    except Exception as e:
        print(f"Error retrieving memories: {e}")
    return ""

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