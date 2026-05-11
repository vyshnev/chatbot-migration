# LangGraph Chatbot

A modern chatbot prototype built with a **React** frontend and a **FastAPI** backend, powered by **LangGraph** for stateful agentic conversations.

## Project Status

This project is an active work-in-progress. The core app structure is in place, including streaming chat, PostgreSQL-backed conversation state, tool calling, and a React UI, but it still needs build/lint cleanup, automated tests, authentication, stricter CORS, and deployment hardening before it should be used beyond local development.

## Features

*   **Modular Architecture**: Business logic cleanly separated into domain-specific modules (`core`, `agent`, `memory`, `threads`, `tools`).
*   **Tool Output UI**: Tool outputs are rendered in collapsible accordion dropdowns, keeping the main chat focused on user and assistant messages.
*   **PostgreSQL Persistence**: Uses `psycopg` connection pooling for app data and LangGraph's `PostgresSaver` for conversation checkpoints.
*   **Tool Caching**: Uses **Upstash Redis** to cache external tool outputs, such as stock queries and web searches, when Redis credentials are configured.
*   **Polished Chat Layout**: Content is horizontally constrained for comfortable reading. The input bar sits at the bottom with a subtle gradient dissolve above it.
*   **Warm Dark Theme**: Warm dark palette (`#171615` background, `#1e1d1c` surfaces) designed for extended reading sessions.
*   **Streaming Responses**: Streams AI response chunks from FastAPI to the React client.
*   **Conversation Management**: Sidebar access to delete, switch between, or start new chat threads.

## Tech Stack

### Frontend
*   **React** (Vite)
*   **Tailwind CSS** (Styling & Theming)
*   **Lucide React** (Icons)
*   **React Markdown** (Rich text & Code rendering)

### Backend
*   **FastAPI** (API Server & NDJSON Streaming)
*   **LangGraph** (Agent Orchestration & Checkpointing)
*   **LangChain** (LLM Interface)
*   **PostgreSQL** (Business Logic & State Persistence via `psycopg_pool`)
*   **Upstash Redis** (Optional Tool Result Caching)

## Installation & Setup

### Prerequisites
*   Python 3.10+
*   Node.js 18+
*   OpenAI API Key
*   PostgreSQL Database URL (e.g., Supabase)
*   Optional: Upstash Redis URL and Token for tool-result caching

### 1. Backend Setup

Navigate to the root directory:

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: install legacy/debug tooling
pip install -r requirements-dev.txt

# Create a .env file with required backend settings
echo "OPENAI_API_KEY=your_api_key_here" > .env
echo "DATABASE_URL=postgresql://user:password@host:port/dbname" >> .env
echo "TAVILY_API=your_api_key_here" >> .env
```

Optional API configuration:

```bash
# Defaults to the Vite local dev origins if omitted.
echo "CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173" >> .env
```

Optional Redis caching:

```bash
# Add these only if you want Upstash-backed tool-result caching.
# Without them, tools still run directly without cached results.
echo "UPSTASH_REDIS_REST_URL=your_redis_url" >> .env
echo "UPSTASH_REDIS_REST_TOKEN=your_redis_token" >> .env
```

Run the backend server:

```bash
python server.py
```
The server will start at `http://localhost:8000`.

### 2. Frontend Setup

Navigate to the frontend directory:

```bash
cd frontend

# Install dependencies
npm install
```

Run the development server:

```bash
npm run dev
```
The application will be available at `http://localhost:5173`.

## Usage

1.  Start both the backend and frontend servers.
2.  Open `http://localhost:5173` in your browser.
3.  Type a message to start chatting!
4.  Use the sidebar to switch between conversation threads, or click the "Chatbot AI" logo to start a fresh chat with a new random greeting.
5.  Watch the AI trigger tools like Web Search or Memory Storage, expanding their output via the accordion UI.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
