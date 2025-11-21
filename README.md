# LangGraph Chatbot

A modern, streaming chatbot application built with a **React** frontend and a **FastAPI** backend, powered by **LangGraph** for stateful agentic conversations.

![Chatbot UI](./frontend/src/assets/react.svg) *(Replace with actual screenshot if available)*

## 🚀 Features

*   **Streaming Responses**: Real-time character-by-character streaming of AI responses.
*   **Context Retention**: Maintains conversation history within a session using thread IDs.
*   **Tool Usage**: Integrated with tools like DuckDuckGo Search and Stock Price checkers.
*   **Markdown Support**: Renders rich text, code blocks, and lists using `react-markdown`.
*   **Modern UI**: Sleek "Matte Black" dark mode design with glassmorphism effects.
*   **Conversation History**: Sidebar access to previous chat threads.

## 🛠️ Tech Stack

### Frontend
*   **React** (Vite)
*   **Tailwind CSS** (Styling)
*   **Lucide React** (Icons)
*   **React Markdown** (Rendering)

### Backend
*   **FastAPI** (API Server)
*   **LangGraph** (Agent Orchestration)
*   **LangChain** (LLM Interface)
*   **SQLite** (State Persistence)

## 📦 Installation & Setup

### Prerequisites
*   Python 3.9+
*   Node.js 16+
*   OpenAI API Key

### 1. Backend Setup

Navigate to the root directory:

```bash
# Install dependencies
pip install -r requirements.txt

# Create a .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
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

## 🏃‍♂️ Usage

1.  Start both the backend and frontend servers.
2.  Open `http://localhost:5173` in your browser.
3.  Type a message to start chatting!
4.  Use the sidebar to switch between conversation threads or start a new chat.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
