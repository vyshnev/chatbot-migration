from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from langgraph_tool_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage
import uuid
import uvicorn
import asyncio

app = FastAPI(title="LangGraph Chatbot API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ThreadResponse(BaseModel):
    threads: List[str]

@app.get("/threads", response_model=ThreadResponse)
async def get_threads():
    """Retrieve all available chat threads."""
    try:
        threads = retrieve_all_threads()
        # Convert to strings just in case
        return {"threads": [str(t) for t in threads]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{thread_id}")
async def get_history(thread_id: str):
    """Retrieve message history for a specific thread."""
    try:
        config = {'configurable': {'thread_id': thread_id}}
        state = chatbot.get_state(config)
        messages = state.values.get('messages', [])
        
        formatted_messages = []
        for msg in messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg.content
            })
            
        return {"messages": formatted_messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import StreamingResponse

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Stream chat response.
    If thread_id is not provided, a new one is generated.
    """
    thread_id = request.thread_id
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    config = {
        'configurable': {'thread_id': thread_id},
        "metadata": {"thread_id": thread_id},
        "run_name": "chat_turn"
    }

    async def event_generator():
        # First yield the thread_id so the frontend knows where to continue
        yield f'{{"type": "thread_id", "content": "{thread_id}"}}\n'
        
        try:
            # We need to run the synchronous langgraph stream in a way that doesn't block the event loop
            # However, langgraph stream might be synchronous. 
            # For simplicity in this MVP, we'll iterate directly if it supports it, 
            # or use run_in_executor if it's strictly blocking.
            # Assuming chatbot.stream is a generator.
            
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=request.message)]},
                config=config,
                stream_mode='messages'
            ):
                if isinstance(message_chunk, AIMessage):
                    # Escape newlines for JSON safety in SSE/stream
                    content = message_chunk.content.replace('\n', '\\n').replace('"', '\\"')
                    yield f'{{"type": "chunk", "content": "{content}"}}\n'
                    
        except Exception as e:
            yield f'{{"type": "error", "content": "{str(e)}"}}\n'

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
