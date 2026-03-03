# System Architecture & Code Documentation

This document provides a comprehensive overview of the LangGraph AI Chatbot project, with a heavy focus on the backend architecture, state management, and API design.

## 1. Backend Architecture (FastAPI & LangGraph)

The backend is built using **FastAPI** for high-performance API routing and **LangGraph** (powered by LangChain) for orchestrating the autonomous AI agent. The system uses **SQLite** for maintaining persistent conversational state over time.

### 1.1 Core Agent Components (`langgraph_tool_backend.py`)

This module encapsulates the entirety of the AI agent's logic, including tools, state management, and direct database interactions.

#### LLM and Tools Initialization
- **LLM Engine**: The system uses `ChatOpenAI` (GPT-4) as the core reasoning engine.
- **Tools Registry**:
  - `search_tool` (DuckDuckGo): Allows the agent to query the web for real-time information.
  - `get_stock_price`: A custom Python tool calling the Alpha Vantage API to fetch real-time financial market data.
  - `calculator`: A robust arithmetic tool designed to securely and deterministically handle mathematical logic outside the LLM.
- **Tool Binding**: Tools are bound to the LLM using `.bind_tools()`. This grants the model the capability to autonomously decide when a user's query requires external execution and how to formulate the parameters.

#### State Management (`ChatState`)
- Defines the agent's memory as a `TypedDict` containing a list of `BaseMessage` objects. It leverages LangGraph's `add_messages` reducer to append new messages to an existing conversation thread seamlessly, preventing data overwrites.

#### LangGraph Orchestration Pipeline
- **Nodes**:
  - `chat_node`: Invokes the LLM with the current conversation history. It decides whether to formulate a final response directly or initiate a tool call.
  - `tool_node`: Executes the requested tool(s) securely and returns the raw results formatting them back into the graph's memory.
- **Edges & Routing**: 
  - A conditional edge evaluates if a tool call was requested by the `chat_node`. If true, it routes to `tool_node`; otherwise, it finishes the run (`END`).
  - The `tool_node` explicitly routes back to the `chat_node` so the LLM can interpret the raw tool output and formulate a coherent response.
- **SQLite Checkpointer (`SqliteSaver`)**: 
  - Tied to a local `chatbot.db`. This enables the graph to pause, persist, and resume state seamlessly using uniquely generated `thread_id`s, ensuring complete memory retention across independent browser sessions and server restarts.

#### Custom Database Management & Helpers
Alongside LangGraph's internal `checkpoints` and `writes` tables, a custom `thread_metadata` table is managed to power the frontend UI capabilities.
- **Schema**: Tracks `thread_id`, `title`, and `last_updated`.
- **`update_thread_timestamp()`**: Updates the `last_updated` field whenever a thread is interacted with, enabling dynamic UI sorting (most recent queries surfaced first).
- **Title Generation**: (`generate_title()`, `save_thread_title()`) When a new chat begins, the system utilizes a lightweight, background LLM invocation to summarize the user's initial prompt into a concise 3-5 word title and saves it to the DB asynchronously.
- **Data Cleanup**: (`retrieve_all_threads()`, `delete_thread()`) Handles fetching the ordered list of conversations and safely executing hard deletes of a thread entirely from the database across all relational tables.

---

### 1.2 REST API Layer (`server.py`)

A FastAPI server exposes the LangGraph backend logic securely to the frontend client.

- **`POST /chat`**: 
  - The core interaction endpoint. It accepts a user string message and an optional `thread_id`.
  - Generates a new `thread_id` (UUID) if none is provided and dynamically spawns a `BackgroundTasks` function to handle title generation without blocking the response.
  - **Streaming Execution**: Returns a `StreamingResponse` using Server-Sent Events (SSE/NDJSON). It iterates over the async `chatbot.stream()`, parsing output chunks and streaming textual AI tokens to the client in real-time as they are yielded by OpenAI.
- **`GET /threads`**: Returns a list of all active conversations to populate the client sidebar, ordered deterministically by the `last_updated` timestamp.
- **`GET /history/{thread_id}`**: Retrieves the complete historical message array for a specific thread directly from the LangGraph SQLite checkpointer (`chatbot.get_state()`), formatting it appropriately (`user` vs `assistant` roles) for the client.
- **`DELETE /threads/{thread_id}`**: Deletes all custom metadata and corresponding native LangGraph state blobs associated with a specific conversation thread.

---

## 2. Frontend Architecture Summary (React & Vite)

The frontend is a modern, responsive Single Page Application built with **React**, **Vite**, and styled entirely with custom **Tailwind CSS**. While standard frontend conventions apply, a few advanced features power the experience:

### Key Technical Details
- **Real-Time Token Streaming**: The core messaging logic within `api.js` utilizes the standard Native Fetch API coupled with the `ReadableStream` interface (`response.body.getReader()`) to process incoming chunked bytes from the `/chat` endpoint. This provides a highly reactive, typing-effect UX without the overhead of WebSockets.
- **State Synchronization**: Strictly adheres to React hooks (`useState`, `useEffect`) to reactively sync the globally active `currentThreadId` flag against the backend history. It dynamically updates the sidebar conversation list whenever net-new AI interactions finish.
- **Markdown & Code Rendering Engine**: Incorporates functional plugins like `react-markdown` and `remark-gfm` to securely parse and render complex AI outputs. This handles nested markdown nodes (like structured tables and bolding) and applies syntax highlighting to code blocks, completely harmonized against the application's global "matte black" custom theme.
