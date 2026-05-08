import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MessageSquare } from 'lucide-react';
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
  const [greeting, setGreeting] = useState(GREETINGS[0]);
  const messagesEndRef = useRef(null);

  const {
    status,
    messages,
    error,
    sendMessage,
    setInitialMessages,
    resetStream,
  } = useChatStream();

  const isStreaming = status === 'STREAMING';

  // Initialize Chat
  useEffect(() => {
    resetStream();
    
    if (chatId) {
      // Load existing history
      const loadHistory = async () => {
        try {
          const data = await chatService.getHistory(chatId);
          setInitialMessages(data.messages);
        } catch (err) {
          console.error('Error loading history:', err);
        }
      };
      loadHistory();
    } else {
      // Setup new chat greeting
      setGreeting(GREETINGS[Math.floor(Math.random() * GREETINGS.length)]);
    }
  }, [chatId, resetStream, setInitialMessages]);

  // Auto-scroll logic
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    
    const content = input;
    setInput('');
    
    // If we're creating a new chat, the hook will call this callback with the new ID
    sendMessage(content, chatId, (newThreadId) => {
      // Only navigate if we are currently on the home page to prevent weird race conditions
      if (!chatId) {
        navigate(`/chat/${newThreadId}`, { replace: true });
      }
    });
  };

  const isNewChat = !chatId && messages.length === 0;

  return (
    <div className="flex-1 flex flex-col overflow-hidden relative w-full h-full">
      {isNewChat ? (
        <div className="h-full flex flex-col items-center justify-center w-full max-w-3xl mx-auto px-4 -mt-10">
          <MessageSquare size={56} className="mb-6 text-gray-600" />
          <h2 className="text-2xl md:text-3xl font-bold text-gray-200 mb-8 text-center">{greeting}</h2>

          <ChatInput 
            input={input} 
            setInput={setInput} 
            onSubmit={handleSubmit} 
            isLoading={isStreaming} 
          />
        </div>
      ) : (
        <>
          <MessageList 
            messages={messages} 
            messagesEndRef={messagesEndRef} 
          />
          
          <div className="py-4 bg-matte-black/95 backdrop-blur border-t border-gray-800 shrink-0">
            <div className="max-w-3xl mx-auto px-4">
              <ChatInput 
                input={input} 
                setInput={setInput} 
                onSubmit={handleSubmit} 
                isLoading={isStreaming} 
              />
            </div>
          </div>
        </>
      )}

      {/* Optional: Simple toast/alert if there's a stream error */}
      {status === 'ERROR' && (
        <div className="absolute top-4 right-4 bg-red-900/90 text-red-100 px-4 py-2 rounded-lg text-sm border border-red-700 shadow-xl z-50">
          Error: {error}
        </div>
      )}
    </div>
  );
}
