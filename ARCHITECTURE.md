# System Architecture & Code Documentation

This document provides a comprehensive overview of the LangGraph AI Chatbot project, with a heavy focus on the backend architecture, state management, and API design.

## 1. Backend Architecture (FastAPI & LangGraph)

The backend is built using **FastAPI** for high-performance API routing and **LangGraph** (powered by LangChain) for orchestrating the autonomous AI agent. The system uses **PostgreSQL** for maintaining persistent conversational state and business data over time.

### 1.1 Modular Domain Structure

The application has been refactored from a single-file monolith into a clean, domain-driven modular architecture:

- **`core/`**: Infrastructure and configuration. Contains `database.py` which manages the `psycopg_pool.ConnectionPool` and executes idempotent schema migrations.
- **`agent/`**: Contains the core LangGraph definition (`graph.py`), LLM initialization, and system prompts.
- **`memory/`**: Services for long-term fact storage (`user_memory` table) allowing the AI to persist knowledge about the user across sessions.
- **`threads/`**: Services for managing chat thread metadata (`thread_metadata` table), handling sidebar history, timestamps, and thread deletion.
- **`tools/`**: The tool registry (`registry.py`) and implementations (e.g., `memory_tools.py` for reading/writing long-term facts, plus search and math tools).

### 1.2 Core Agent Components

#### LLM and Tools Initialization
- **LLM Engine**: Uses `ChatOpenAI` (e.g., GPT-4o) as the core reasoning engine.
- **Optional Caching Layer (Upstash Redis)**: 
  - External API tools are wrapped with a custom cache decorator.
  - Uses **Upstash Redis** to store deterministic JSON results when Redis credentials are configured.
  - If Redis is not configured or cache access fails, tools fall back to direct execution.
- **Dependency Injection**: Database connection pools are injected into services at startup (`langgraph_tool_backend.py`), allowing business logic to run without circular imports.

#### LangGraph Orchestration Pipeline
- **Nodes & Edges**: The graph routes between a `chat_node` (LLM reasoning) and a `tool_node` (external execution). If the LLM requests a tool, the graph executes it and loops back to the LLM until a final response is ready.
- **PostgreSQL Checkpointer (`PostgresSaver`)**: 
  - The agent's short-term memory (conversation turns) is securely persisted in PostgreSQL using LangGraph's native Postgres checkpointer.
  - A separate, persistent `autocommit=True` connection is dedicated to the checkpointer to avoid transaction collisions with standard business logic.

---

### 1.3 REST API Layer (`server.py`)

A FastAPI server exposes the LangGraph backend logic securely to the frontend client.

- **`POST /chat`**: 
  - The core interaction endpoint. It accepts a user string message and an optional `thread_id`.
  - **Streaming Execution**: Returns newline-delimited JSON (`application/x-ndjson`) with `thread_id`, `chunk`, and `error` events. The React client reads the stream incrementally with `ReadableStream`.
- **`GET /threads`**: Returns a list of all active conversations to populate the client sidebar, ordered deterministically by the `last_updated` timestamp.
- **`GET /history/{thread_id}`**: Retrieves the complete historical message array for a specific thread directly from the LangGraph checkpointer, formatting roles (user/assistant/tool).
- **`DELETE /threads/{thread_id}`**: Executes a cascading deletion across both custom business tables and native LangGraph state tables to fully scrub a conversation.

---

## 2. Frontend Architecture Summary (React & Vite)

The frontend is a modern, responsive Single Page Application built with **React**, **Vite**, and styled entirely with custom **Tailwind CSS**. 

### Key Technical Details
- **Global State Management**: Uses **Zustand** (`useChatStore`) to manage sidebar visibility, active thread lists, and cross-component communication efficiently without prop-drilling.
- **Real-Time Token Streaming**: Custom hooks utilize the Native Fetch API and the `ReadableStream` interface (`response.body.getReader()`) to process incoming chunked bytes from the `/chat` endpoint.
- **Agentic UI Patterns**: 
  - "Industry-standard" constrained reading widths align the input bar and chat messages perfectly.
  - Raw tool executions (e.g., "Web Search", "Memory Updated") are intercepted and rendered as collapsible **Accordion pills (▽)**, ensuring the main chat feed remains uncluttered.
- **Markdown & Code Rendering**: Incorporates `react-markdown` and `remark-gfm` to securely parse and render complex AI outputs, including nested tables and syntax-highlighted code blocks.
- **Warm Dark Theme**: The entire application uses a carefully curated warm-gray palette (`#171615` backgrounds, `#1e1d1c` surfaces, `#d6d5d4` text) to reduce eye strain during extended reading sessions, complete with a seamless gradient-dissolve above the input bar.
