import React, { useEffect } from 'react';
import { Outlet, useNavigate, useParams, useLocation } from 'react-router-dom';
import clsx from 'clsx';
import { Menu, X, Plus } from 'lucide-react';
import { SidebarHistory } from '../components/sidebar/SidebarHistory';
import { useChatStore } from '../store/useChatStore';
import ErrorBoundary from '../ErrorBoundary';

export function MainLayout() {
  const navigate = useNavigate();
  const { chatId } = useParams();
  
  // Extract state from Zustand
  const threads = useChatStore((state) => state.threads);
  const loadThreads = useChatStore((state) => state.loadThreads);
  const deleteThread = useChatStore((state) => state.deleteThread);
  const isSidebarOpen = useChatStore((state) => state.isSidebarOpen);
  const setSidebarOpen = useChatStore((state) => state.setSidebarOpen);

  useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  const handleNewChat = () => {
    navigate('/');
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  const handleSelectThread = (id) => {
    navigate(`/chat/${id}`);
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  const handleDeleteThread = async (id) => {
    const success = await deleteThread(id);
    if (success && chatId === id) {
      navigate('/');
    }
  };

  return (
    <div className="flex h-screen bg-matte-black text-white overflow-hidden font-sans">
      {/* Sidebar */}
      <div className={clsx(
        "fixed inset-y-0 left-0 z-50 w-64 bg-matte-black border-r border-warm-surface transition-transform duration-300 ease-in-out transform",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full",
        "md:relative md:translate-x-0"
      )}>
        <div className="p-4 flex flex-col h-full">
          <div className="flex items-center justify-between mb-6">
            <h1
              onClick={handleNewChat}
              className="text-xl font-bold text-warm-text cursor-pointer hover:text-warm-text/70 transition-colors"
              title="Start new chat"
            >
              Chatbot AI
            </h1>
            <button onClick={() => setSidebarOpen(false)} className="md:hidden p-1 hover:bg-warm-surface rounded">
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

          <SidebarHistory 
            threads={threads}
            activeThreadId={chatId}
            onSelect={handleSelectThread}
            onDelete={handleDeleteThread}
          />
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full relative">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center p-4 border-b border-warm-surface bg-matte-black/95 backdrop-blur z-40">
          <button onClick={() => setSidebarOpen(true)} className="p-2 hover:bg-warm-surface rounded-lg mr-3">
            <Menu size={24} />
          </button>
          <span className="font-bold">Chatbot AI</span>
        </div>

        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </div>
    </div>
  );
}
