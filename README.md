# LangGraph Chatbot

A modern, streaming chatbot application built with a **React** frontend and a **FastAPI** backend, powered by **LangGraph** for stateful agentic conversations.

## Features

*   **Streaming Responses**: Real-time character-by-character streaming of AI responses, powered by FastAPI threaded SSE generators.
*   **Context Retention**: Maintains conversation history within a session using SQLite thread checkpoints.
*   **Agentic UI**: Tool outputs are cleanly tucked away into collapsible dropdowns, keeping the main chat clean and focusing on final LLM responses. "Ghost bubbles" from tool execution are seamlessly filtered out.
*   **Tool Caching**: Integrated **Upstash Redis** to deterministically cache external tool outputs (like Stock queries or Web searches) to reduce latency and protect rate limits.
*   **ChatGPT-style UI**: Empty state screen features randomized greetings and a perfectly centered input box that naturally snaps to the bottom once the conversation starts.
*   **Conversation Management**: Sidebar access to delete, switch between, or start new chat threads (the app title is also clickable to quick-start a new session).
*   **Markdown Support**: Renders rich text, code blocks, and lists using `react-markdown`.
*   **Modern Aesthetics**: Sleek "Matte Black" dark mode design with Tailwind CSS glassmorphism effects and micro-animations.

## Tech Stack

### Frontend
*   **React** (Vite)
*   **Tailwind CSS** (Styling)
*   **Lucide React** (Icons)
*   **React Markdown** (Rendering)

### Backend
*   **FastAPI** (API Server & SSE Streaming)
*   **LangGraph** (Agent Orchestration)
*   **LangChain** (LLM Interface)
*   **SQLite** (State Persistence & History)
*   **Upstash Redis** (Tool Result Caching)

## Installation & Setup

### Prerequisites
*   Python 3.9+
*   Node.js 16+
*   OpenAI API Key
*   Upstash Redis URL and Token

### 1. Backend Setup

Navigate to the root directory:

```bash
# Install dependencies
pip install -r requirements.txt

# Create a .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
