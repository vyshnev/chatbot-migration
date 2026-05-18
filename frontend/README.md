# Chatbot Frontend

This is the React + Vite frontend for the LangGraph Chatbot project. It provides a polished, dark-themed interface for interacting with the AI assistant, featuring real-time streaming, thread management, and PDF document uploading.

## Tech Stack

- **Framework**: [React 18](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **HTTP Client**: [Axios](https://axios-http.com/)
- **Markdown Rendering**: [react-markdown](https://github.com/remarkjs/react-markdown) with syntax highlighting
- **Testing**: [Playwright](https://playwright.dev/) for E2E tests

## Setup & Installation

Ensure you have Node.js 18+ installed.

```bash
# Install dependencies
npm install
```

### Environment Variables

Create a `.env.local` file in the `frontend` directory if your backend is hosted somewhere other than `http://localhost:8000`.

```env
# Optional: Set this if your backend is running on a different port or host
VITE_API_URL=http://localhost:8000
```

## Running the Development Server

```bash
npm run dev
```

This will start the Vite development server, usually accessible at `http://localhost:5173`.

## Testing

This project uses Playwright for end-to-end (E2E) testing to verify core functionality like streaming and navigation.

```bash
# Run tests headlessly
npm run test

# Run tests with the Playwright UI
npm run test:ui
```

> **Note**: E2E tests require the backend server to be running. If the backend is not on `http://localhost:8000`, configure the appropriate URL in `playwright.config.js`.

## Troubleshooting

- **Upload Failed**: Ensure the backend server is running and you haven't manually overridden the `Content-Type` header when using Axios `FormData`.
- **Stream Not Starting**: Check that the backend server is reachable. If you get CORS errors, verify `CORS_ALLOWED_ORIGINS` on the backend `.env`.
- **UI Layout Breaks**: Check Tailwind class combinations. The input bar uses a complex flex layout to accommodate the pending file chip and multi-line textareas.

