# LangGraph Chatbot

A modern, production-ready chatbot application built with a **React** frontend and a **FastAPI** backend, powered by **LangGraph** for stateful agentic conversations.

## Features

*   **Modular Architecture**: Business logic cleanly separated into domain-specific modules (`core`, `agent`, `memory`, `threads`, `tools`).
*   **Agentic UI**: Tool outputs are cleanly tucked away into collapsible accordion dropdowns, keeping the main chat clean and focusing on final LLM responses. "Ghost bubbles" from tool execution are seamlessly filtered out.
*   **Enterprise Persistence**: Fully migrated to **PostgreSQL** (via Supabase) using `psycopg` connection pooling for long-running stability, and LangGraph's `PostgresSaver` for resilient conversational memory.
*   **Tool Caching**: Integrated **Upstash Redis** to deterministically cache external tool outputs (like Stock queries or Web searches) to reduce latency and protect rate limits.
*   **Industry-Standard UI**: Content is horizontally constrained for optimal reading (like Claude/ChatGPT). The input bar floats naturally at the bottom with a subtle gradient dissolve, removing harsh borders.
*   **Warm Dark Theme**: Sleek, eye-strain-reducing warm dark palette (`#171615` background, `#1e1d1c` surfaces) designed for extended reading sessions.
*   **Streaming Responses**: Real-time character-by-character streaming of AI responses, powered by FastAPI threaded SSE generators.
*   **Conversation Management**: Sidebar access to delete, switch between, or start new chat threads.

## Tech Stack

### Frontend
*   **React** (Vite)
*   **Tailwind CSS** (Styling & Theming)
*   **Lucide React** (Icons)
*   **React Markdown** (Rich text & Code rendering)

### Backend
*   **FastAPI** (API Server & SSE Streaming)
*   **LangGraph** (Agent Orchestration & Checkpointing)
*   **LangChain** (LLM Interface)
*   **PostgreSQL** (Business Logic & State Persistence via `psycopg_pool`)
*   **Upstash Redis** (Tool Result Caching)

## Installation & Setup

### Prerequisites
*   Python 3.10+
*   Node.js 18+
*   OpenAI API Key
*   PostgreSQL Database URL (e.g., Supabase)
*   Upstash Redis URL and Token

### 1. Backend Setup

Navigate to the root directory:

```bash
# Install dependencies
pip install -r requirements.txt

# Create a .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
echo "DATABASE_URL=postgresql://user:password@host:port/dbname" >> .env
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
