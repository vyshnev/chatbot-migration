import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MessageSquare, FileText } from 'lucide-react';
import { useChatStream } from '../hooks/useChatStream';
import { chatService } from '../services/chatService';
import { MessageList } from '../components/chat/MessageList';
import { ChatInput } from '../components/chat/ChatInput';

const GREETINGS = [
  "How can I help you today?",
  "Where should we start?",
  "Where should we begin?",
  "What's on your mind today?",
  "What's on the agenda today?",
  "Ready to brainstorm?",
  "What can I help you discover?"
];

export function ChatPage() {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [historyError, setHistoryError] = useState(false);
  const [greeting] = useState(
    () => GREETINGS[Math.floor(Math.random() * GREETINGS.length)]
  );
  const messagesEndRef = useRef(null);

  // PDF files uploaded to the current thread
  const [threadFiles, setThreadFiles] = useState([]);
  
  // File staged for upload before a thread exists
  const [pendingFile, setPendingFile] = useState(null);

  const {
    status,
    messages,
    error,
    sendMessage,
    setInitialMessages,
    resetStream,
    abortStream,
  } = useChatStream();

  const isStreaming = status === 'STREAMING';

  // Fetch the list of PDFs uploaded to this thread
  const fetchThreadFiles = useCallback(async (id) => {
    if (!id) { setThreadFiles([]); return; }
    try {
      const data = await chatService.getThreadFiles(id);
      setThreadFiles(data.files ?? []);
    } catch {
      // Non-critical — silently ignore
    }
  }, []);

  // Initialize Chat
  useEffect(() => {
    resetStream();
    setHistoryError(false);
    setThreadFiles([]);
    setPendingFile(null);

    if (chatId) {
      // Load history and uploaded files in parallel
      const loadHistory = async () => {
        try {
          const data = await chatService.getHistory(chatId);
          setInitialMessages(data.messages);
        } catch (err) {
          console.error('Error loading history:', err);
          setHistoryError(true);
        }
      };
      loadHistory();
      fetchThreadFiles(chatId);
    }
  }, [chatId, resetStream, setInitialMessages, fetchThreadFiles]);

  // Auto-scroll logic
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if ((!input.trim() && !pendingFile) || isStreaming) return;

    const content = input.trim() || "Analyze the uploaded document.";
    setInput('');

    // If we're creating a new chat, the hook will call this callback with the new ID
    sendMessage(content, chatId, async (newThreadId) => {
      // If we have a pending file, upload it to the newly created thread before navigating
      if (pendingFile) {
        try {
          await chatService.uploadFile(pendingFile, newThreadId);
        } catch (err) {
          console.error("Failed to upload pending file to new thread:", err);
        }
        setPendingFile(null);
      }

      // Only navigate if we are currently on the home page to prevent weird race conditions
      if (!chatId) {
        navigate(`/chat/${newThreadId}`, { replace: true });
      }
    });
  };

  const isNewChat = !chatId && messages.length === 0;

  // Shared ChatInput props
  const chatInputProps = {
    input,
    setInput,
    onSubmit: handleSubmit,
    onAbort: abortStream,
    isLoading: isStreaming,
    threadId: chatId,
    onUploadComplete: () => fetchThreadFiles(chatId),
    pendingFile,
    onPendingFileSet: setPendingFile,
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden relative w-full h-full">
      {isNewChat ? (
        <div className="h-full flex flex-col items-center justify-center w-full max-w-3xl mx-auto px-4 -mt-10">
          <MessageSquare size={56} className="mb-6 text-gray-600" />
          <h2 className="text-2xl md:text-3xl font-bold text-gray-200 mb-8 text-center">{greeting}</h2>

          <ChatInput {...chatInputProps} threadId={null} />
        </div>
      ) : (
        <>
          {/* Message area — gradient overlay dissolves the last message into the input bar */}
          <div className="relative flex-1 min-h-0 flex flex-col">
            <MessageList
              messages={messages}
              messagesEndRef={messagesEndRef}
            />
            <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-matte-black to-transparent z-10" />
          </div>

          <div className="py-4 bg-matte-black shrink-0">
            <div className="max-w-3xl mx-auto px-4">
              {/* Active files chip — shows which PDFs are available in this thread */}
              {threadFiles.length > 0 && (
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  {threadFiles.map((f) => (
                    <div
                      key={f.filename}
                      title={`${f.chunks} chunks indexed`}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#1e1d1b] border border-[#2e2d2b] text-[11px] text-warm-muted/70"
                    >
                      <FileText size={11} className="text-emerald-400 shrink-0" />
                      <span className="truncate max-w-[180px]">{f.filename}</span>
                    </div>
                  ))}
                  <span className="text-[10px] text-warm-muted/35 ml-1">active in this chat</span>
                </div>
              )}

              <ChatInput {...chatInputProps} />
            </div>
          </div>
        </>
      )}

      {/* History load failure banner */}
      {historyError && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 w-full max-w-xl px-4 z-50">
          <div className="flex items-center justify-between gap-3 bg-yellow-900/80 text-yellow-100 px-4 py-2.5 rounded-lg text-sm border border-yellow-700/60 shadow-xl backdrop-blur">
            <span>⚠️ Could not load chat history. The AI will respond without prior context.</span>
            <button
              onClick={() => setHistoryError(false)}
              className="text-yellow-300 hover:text-white transition-colors shrink-0 font-bold"
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Stream error toast */}
      {status === 'ERROR' && (
        <div className="absolute top-4 right-4 bg-red-900/90 text-red-100 px-4 py-2 rounded-lg text-sm border border-red-700 shadow-xl z-50">
          Error: {error}
        </div>
      )}
    </div>
  );
}
