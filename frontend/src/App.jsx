import { useState, useEffect, useRef } from 'react';
import { getThreads, getHistory, streamChat, deleteThread } from './api';
import { MessageSquare, Plus, Send, Menu, X, Trash2, Wrench } from 'lucide-react';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const GREETINGS = [
  "How can I help you today?",
  "Where should we start?",
  "Where should we begin?",
  "What's on your mind today?",
  "What's on the agenda today?",
  "Ready to brainstorm?",
  "What can I help you discover?"
];

function App() {
  const [threads, setThreads] = useState([]);
  const [currentThreadId, setCurrentThreadId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [greeting, setGreeting] = useState(GREETINGS[0]);
  const messagesEndRef = useRef(null);

  // Randomize greeting when starting a new chat
  useEffect(() => {
    if (!currentThreadId) {
      setGreeting(GREETINGS[Math.floor(Math.random() * GREETINGS.length)]);
    }
  }, [currentThreadId]);

  useEffect(() => {
    loadThreads();
  }, []);

  useEffect(() => {
    if (currentThreadId) {
      loadHistory(currentThreadId);
    } else {
      setMessages([]);
    }
  }, [currentThreadId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadThreads = async () => {
    try {
      const data = await getThreads();
      setThreads(data.threads);
    } catch (error) {
      console.error('Error loading threads:', error);
    }
  };

  const loadHistory = async (threadId) => {
    try {
      const data = await getHistory(threadId);
      setMessages(data.messages);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const handleNewChat = () => {
    setCurrentThreadId(null);
    setMessages([]);
  };

  const handleDeleteThread = async (e, threadId) => {
    e.stopPropagation();
    e.stopPropagation();
    // if (!confirm('Are you sure you want to delete this chat?')) return;

    try {
      await deleteThread(threadId);
      setThreads(prev => prev.filter(t => t.id !== threadId));
      if (currentThreadId === threadId) {
        handleNewChat();
      }
    } catch (error) {
      console.error('Error deleting thread:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    let assistantMessage = { role: 'assistant', content: '' };
    setMessages(prev => [...prev, assistantMessage]);

    let newThreadId = null;

    await streamChat(
      userMessage.content,
      currentThreadId,
      (chunk) => {
        setMessages(prev => {
          const newMessages = [...prev];
          const lastMsgIndex = newMessages.length - 1;
          const lastMsg = { ...newMessages[lastMsgIndex] };
          lastMsg.content += chunk;
          newMessages[lastMsgIndex] = lastMsg;
          return newMessages;
        });
      },
      () => {
        setIsLoading(false);
        if (!currentThreadId && newThreadId) {
          setCurrentThreadId(newThreadId);
        }
        loadThreads(); // Refresh threads list to get the new one if it was new
      },
      (error) => {
        console.error('Chat error:', error);
        setIsLoading(false);
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error}` }]);
      },
      (id) => {
        newThreadId = id;
      }
    );
  };

  return (
    <div className="flex h-screen bg-matte-black text-white overflow-hidden font-sans">
      {/* Sidebar */}
      <div className={clsx(
        "fixed inset-y-0 left-0 z-50 w-64 bg-matte-black border-r border-gray-700 transition-transform duration-300 ease-in-out transform",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full",
        "md:relative md:translate-x-0"
      )}>
        <div className="p-4 flex flex-col h-full">
          <div className="flex items-center justify-between mb-6">
            <h1
              onClick={handleNewChat}
              className="text-xl font-bold text-white cursor-pointer hover:text-gray-300 transition-colors"
              title="Start new chat"
            >
              Chatbot AI
            </h1>
            <button onClick={() => setIsSidebarOpen(false)} className="md:hidden p-1 hover:bg-gray-700 rounded">
              <X size={20} />
            </button>
          </div>

          <button
            onClick={handleNewChat}
            className="flex items-center justify-center gap-2 w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 rounded-xl transition-colors font-medium mb-6 shadow-lg shadow-blue-900/20"
          >
            <Plus size={20} />
            New Chat
          </button>

          <div className="flex-1 overflow-y-auto space-y-2 pr-2 scrollbar-thin scrollbar-thumb-gray-700">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2">History</div>
            {threads.map(thread => (
              <button
                key={thread.id}
                onClick={() => setCurrentThreadId(thread.id)}
                className={clsx(
                  "w-full text-left p-3 rounded-lg text-sm transition-all duration-200 flex items-center gap-3 truncate",
                  currentThreadId === thread.id
                    ? "bg-gray-700/50 text-white shadow-sm border border-gray-600/50"
                    : "text-gray-400 hover:bg-gray-800 hover:text-gray-200",
                  "group"
                )}
              >
                <div className="flex items-center min-w-0 flex-1">
                  <span className="truncate">{thread.title}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteThread(e, thread.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 hover:text-red-400 rounded transition-all"
                  title="Delete chat"
                >
                  <Trash2 size={14} />
                </button>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full relative">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center p-4 border-b border-gray-800 bg-matte-black/95 backdrop-blur">
          <button onClick={() => setIsSidebarOpen(true)} className="p-2 hover:bg-gray-800 rounded-lg mr-3">
            <Menu size={24} />
          </button>
          <span className="font-bold">Chatbot AI</span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-thin scrollbar-thumb-gray-700">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center w-full max-w-3xl mx-auto px-4 -mt-10">
              <MessageSquare size={56} className="mb-6 text-gray-600" />
              <h2 className="text-2xl md:text-3xl font-bold text-gray-200 mb-8 text-center">{greeting}</h2>

              {/* Centered Input Area */}
                <form onSubmit={handleSendMessage} className="w-full relative flex items-end gap-2 shadow-2xl bg-gray-800/80 border border-gray-700 rounded-2xl p-2 transition-all">
                  <textarea
                    value={input}
                    onChange={(e) => {
                      setInput(e.target.value);
                      e.target.style.height = 'auto';
                      e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if (input.trim() && !isLoading) handleSendMessage(e);
                      }
                    }}
                    placeholder="Ask anything"
                    className="flex-1 bg-transparent text-white py-2.5 px-4 focus:outline-none placeholder-gray-500 text-base resize-none overflow-y-auto max-h-[200px]"
                    rows="1"
                    disabled={isLoading}
                    autoFocus
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className="p-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white transition-all shadow-lg shadow-blue-900/20 mb-0.5 mr-0.5"
                  >
                    <Send size={20} />
                  </button>
                </form>
            </div>
          ) : (
            messages.map((msg, idx) => {
              if (msg.role === 'tool') {
                return (
                  <div key={idx} className="flex w-full justify-start pl-4 md:pl-12">
                    <details className="text-sm text-gray-400 bg-gray-800/50 border border-gray-700/50 p-2.5 rounded-lg cursor-pointer group max-w-[85%] md:max-w-[70%] shadow-sm">
                      <summary className="flex items-center gap-2 font-medium outline-none select-none hover:text-gray-200 transition-colors">
                        <Wrench size={14} className="text-blue-400" />
                        <span>Used tool: <span className="text-blue-300">{msg.name || 'External Tool'}</span></span>
                      </summary>
                      <div className="mt-3 pt-3 border-t border-gray-700/50">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap text-gray-500 font-mono">
                          {msg.content}
                        </pre>
                      </div>
                    </details>
                  </div>
                );
              }

              return (
                <div
                  key={idx}
                  className={clsx(
                    "flex w-full",
                    msg.role === 'user' ? "justify-end" : "justify-start"
                  )}
                >
                  <div
                    className={clsx(
                      "max-w-[85%] md:max-w-[70%] rounded-2xl p-4 shadow-md leading-relaxed",
                      msg.role === 'user'
                        ? "bg-blue-600 text-white rounded-br-none"
                        : "bg-gray-800 text-gray-100 border border-gray-700 rounded-bl-none"
                    )}
                  >
                    <div className="prose prose-invert max-w-none break-words">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          pre: ({ node, ...props }) => (
                            <div className="overflow-auto w-full my-2 bg-matte-black/50 p-2 rounded-lg">
                              <pre {...props} />
                            </div>
                          ),
                          code: ({ node, ...props }) => (
                            <code className="bg-matte-black/50 rounded px-1" {...props} />
                          )
                        }}
                      >
                        {msg.content || ''}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Bottom Input Area (Only visible when chatting) */}
        {messages.length > 0 && (
          <div className="p-4 md:p-6 bg-matte-black/95 backdrop-blur border-t border-gray-800 transition-all duration-300">
            <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto relative flex items-end gap-2 bg-gray-800 border border-gray-700 rounded-2xl p-2 transition-all">
              <textarea
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (input.trim() && !isLoading) handleSendMessage(e);
                  }
                }}
                placeholder="Type a message..."
                className="flex-1 bg-transparent text-white py-2.5 px-4 focus:outline-none placeholder-gray-500 text-base resize-none overflow-y-auto max-h-[200px]"
                rows="1"
                disabled={isLoading}
                autoFocus
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="p-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white transition-all shadow-lg shadow-blue-900/20 mb-0.5 mr-0.5"
              >
                <Send size={20} />
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
