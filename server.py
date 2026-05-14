import json
from langsmith import uuid7
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langgraph_tool_backend import chatbot
from core.config import CORS_ALLOWED_ORIGINS
from core.logger import get_logger
from threads.service import get_all_threads, generate_title, save_title, update_timestamp, delete_thread
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

logger = get_logger(__name__)

app = FastAPI(title="LangGraph Chatbot API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32000)
    thread_id: Optional[str] = None

class ThreadItem(BaseModel):
    id: str
    title: str

class ThreadResponse(BaseModel):
    threads: List[ThreadItem]


def ndjson_event(event_type: str, content) -> str:
    """Serialize one newline-delimited JSON event."""
    return json.dumps(
        {"type": event_type, "content": content},
        ensure_ascii=False,
    ) + "\n"


def generate_and_save_title(thread_id: str, message: str) -> None:
    """Generate and persist a title without blocking chat response setup."""
    try:
        save_title(thread_id, generate_title(message))
    except Exception:
        logger.exception("Failed to generate title for thread %s", thread_id)


@app.get("/threads", response_model=ThreadResponse)
async def get_threads():
    """Retrieve all available chat threads."""
    try:
        threads = get_all_threads()
        # threads is now a list of dicts {'id': str, 'title': str}
        return {"threads": threads}
    except Exception:
        logger.exception("Failed to retrieve threads")
        raise HTTPException(status_code=500, detail="Failed to retrieve threads")

@app.delete("/threads/{thread_id}")
async def delete_thread_endpoint(thread_id: str):
    """Delete a specific chat thread."""
    try:
        success = delete_thread(thread_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete thread")
        return {"status": "success", "message": f"Thread {thread_id} deleted"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete thread %s", thread_id)
        raise HTTPException(status_code=500, detail="Failed to delete thread")

@app.get("/history/{thread_id}")
async def get_history(thread_id: str):
    """Retrieve message history for a specific thread."""
    try:
        config = {'configurable': {'thread_id': thread_id}}
        state = chatbot.get_state(config)
        messages = state.values.get('messages', [])
        
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, ToolMessage):
                role = "tool"
            else:
                role = "assistant"
                
            # Skip empty assistant messages (tool call triggers)
            if role == "assistant" and not msg.content.strip():
                continue
                
            formatted_messages.append({
                "role": role,
                "content": msg.content,
                "name": getattr(msg, 'name', 'tool') if role == "tool" else None
            })
            
        return {"messages": formatted_messages}
    except Exception:
        logger.exception("Failed to retrieve history for thread %s", thread_id)
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

@app.post("/chat")
def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Stream chat response as newline-delimited JSON.
    If thread_id is not provided, a new one is generated.
    """
    thread_id = request.thread_id
    is_new_thread = False
    if not thread_id:
        thread_id = str(uuid7())
        is_new_thread = True
    
    # Update timestamp for every interaction
    update_timestamp(thread_id)
    
    if is_new_thread:
        background_tasks.add_task(generate_and_save_title, thread_id, request.message)
    
    config = {
        'configurable': {'thread_id': thread_id},
        "metadata": {"thread_id": thread_id},
        "run_name": "chat_turn"
    }

    def event_generator():
        # First yield the thread_id so the frontend knows where to continue
        yield ndjson_event("thread_id", thread_id)
        
        try:
            for message_chunk, _metadata in chatbot.stream(
                {'messages': [HumanMessage(content=request.message)]},
                config=config,
                stream_mode='messages'
            ):
                if isinstance(message_chunk, AIMessage):
                    content = message_chunk.content
                    if not isinstance(content, str):
                        content = json.dumps(content, ensure_ascii=False)
                    yield ndjson_event("chunk", content)
                    
        except Exception:
            logger.exception("Chat stream failed for thread %s", thread_id)
            yield ndjson_event("error", "Chat stream failed. Please try again.")

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
