import json
from contextlib import asynccontextmanager
from langsmith import uuid7
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
from langgraph_tool_backend import chatbot, business_pool, lg_pool
from core.config import CORS_ALLOWED_ORIGINS
from core.logger import get_logger
from threads.service import get_all_threads, generate_title, save_title, update_timestamp, delete_thread, pin_thread, rename_thread
from tools.scraper import cleanup_old_chunks
from tools.document_rag import ingest_pdf, list_thread_files
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter — 20 requests per minute per IP on the /chat endpoint.
# Protects against runaway API costs from abusive or buggy clients.
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app):
    """Run startup tasks then yield; close all pools cleanly on shutdown."""
    # Purge web_scrape chunks older than 30 days on every startup
    cleanup_old_chunks()

    yield
    logger.info("Server shutting down — closing database pools.")
    business_pool.close()
    lg_pool.close()


app = FastAPI(title="LangGraph Chatbot API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    is_pinned: bool = False

class PinRequest(BaseModel):
    pinned: bool

class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

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
            raise HTTPException(status_code=404, detail="Thread not found")
        return {"status": "success", "message": f"Thread {thread_id} deleted"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete thread %s", thread_id)
        raise HTTPException(status_code=500, detail="Failed to delete thread")

@app.patch("/threads/{thread_id}/pin")
async def pin_thread_endpoint(thread_id: str, body: PinRequest):
    """Pin or unpin a chat thread."""
    try:
        success = pin_thread(thread_id, body.pinned)
        if not success:
            raise HTTPException(status_code=404, detail="Thread not found")
        return {"status": "success", "is_pinned": body.pinned}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to pin thread %s", thread_id)
        raise HTTPException(status_code=500, detail="Failed to pin thread")

@app.patch("/threads/{thread_id}/rename")
async def rename_thread_endpoint(thread_id: str, body: RenameRequest):
    """Rename a chat thread."""
    try:
        success = rename_thread(thread_id, body.title)
        if not success:
            raise HTTPException(status_code=404, detail="Thread not found")
        return {"status": "success", "title": body.title}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to rename thread %s", thread_id)
        raise HTTPException(status_code=500, detail="Failed to rename thread")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), thread_id: str = Form(...)):
    """
    Upload a PDF file and ingest it into the vector store for this thread.
    The file is chunked, embedded, and stored with source_type='pdf_upload'
    so it is immune to the 30-day TTL applied to web_scrape chunks.
    """
    # Validate file type
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Read and validate size (max 10 MB)
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds the 10 MB limit.")

    try:
        result = ingest_pdf(file_bytes, file.filename, thread_id)
    except Exception:
        logger.exception("Failed to ingest PDF '%s' for thread %s", file.filename, thread_id)
        raise HTTPException(status_code=500, detail="Failed to process the uploaded file.")

    if result["status"] == "empty":
        raise HTTPException(
            status_code=422,
            detail="The PDF contains no extractable text. Image-only PDFs are not supported.",
        )
    if result["status"] == "duplicate":
        return {"status": "duplicate", "message": "This file has already been uploaded to this conversation."}

    logger.info("Uploaded '%s' (%d chunks) to thread %s", file.filename, result["chunks"], thread_id)
    return {"status": "success", "filename": result["filename"], "chunks": result["chunks"]}


@app.get("/threads/{thread_id}/files")
async def get_thread_files(thread_id: str):
    """List PDF files that have been uploaded to a specific thread."""
    try:
        files = list_thread_files(thread_id)
        return {"files": files}
    except Exception:
        logger.exception("Failed to list files for thread %s", thread_id)
        raise HTTPException(status_code=500, detail="Failed to retrieve file list.")

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
@limiter.limit("20/minute")
def chat_endpoint(request: Request, body: ChatRequest, background_tasks: BackgroundTasks):
    """
    Stream chat response as newline-delimited JSON.
    If thread_id is not provided, a new one is generated.
    """
    thread_id = body.thread_id
    is_new_thread = False
    
    if not thread_id:
        thread_id = str(uuid7())
        is_new_thread = True
    else:
        # Check if the thread exists in metadata; if not, it's a new client-generated thread
        with business_pool.connection() as conn:
            cursor = conn.execute("SELECT 1 FROM thread_metadata WHERE thread_id = %s", (thread_id,))
            if not cursor.fetchone():
                is_new_thread = True

    # Update timestamp for every interaction
    update_timestamp(thread_id)

    if is_new_thread:
        background_tasks.add_task(generate_and_save_title, thread_id, body.message)
    
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
                {'messages': [HumanMessage(content=body.message)]},
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
