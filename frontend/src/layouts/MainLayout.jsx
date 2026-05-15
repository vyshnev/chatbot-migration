import React, { useEffect, useState } from 'react';
import { Outlet, useNavigate, useParams } from 'react-router-dom';
import clsx from 'clsx';
import { Menu, X, Plus, PanelLeft, SquarePen } from 'lucide-react';
import { SidebarHistory } from '../components/sidebar/SidebarHistory';
import { useChatStore } from '../store/useChatStore';
import ErrorBoundary from '../ErrorBoundary';

export function MainLayout() {
  const navigate = useNavigate();
  const { chatId } = useParams();

  // Local UI state — desktop collapse preference
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Extract state from Zustand
  const threads = useChatStore((state) => state.threads);
  const loadThreads = useChatStore((state) => state.loadThreads);
  const deleteThread = useChatStore((state) => state.deleteThread);
  const pinThread = useChatStore((state) => state.pinThread);
  const renameThread = useChatStore((state) => state.renameThread);
  const isSidebarOpen = useChatStore((state) => state.isSidebarOpen);
  const setSidebarOpen = useChatStore((state) => state.setSidebarOpen);
  const storeError = useChatStore((state) => state.error);
  const clearError = useChatStore((state) => state.clearError);

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

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <div className={clsx(
        // Base: slide transition for mobile, width transition for desktop
        "fixed inset-y-0 left-0 z-50 bg-[#1e1d1b] border-r border-warm-surface",
        "transition-all duration-300 ease-in-out",
        // Mobile: always w-64, slide in/out
        "w-64",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full",
        // Desktop: always visible, width driven by collapsed state
        "md:relative md:translate-x-0",
        sidebarCollapsed ? "md:w-12" : "md:w-64",
      )}>

        {sidebarCollapsed ? (
          /* ── Collapsed mini-strip (desktop only) ── */
          <div className="hidden md:flex flex-col items-center pt-3 gap-1 h-full overflow-hidden">
            {/* Expand sidebar */}
            <button
              onClick={() => setSidebarCollapsed(false)}
              className="p-2.5 rounded-lg text-warm-muted hover:bg-[#242321] hover:text-warm-text transition-colors"
              title="Expand sidebar"
            >
              <PanelLeft size={17} />
            </button>
            {/* New chat */}
            <button
              onClick={handleNewChat}
              className="p-2.5 rounded-lg text-warm-muted hover:bg-[#242321] hover:text-warm-text transition-colors"
              title="New chat"
            >
              <SquarePen size={17} />
            </button>
          </div>
        ) : (
          /* ── Full expanded sidebar ── */
          <div className="pl-4 pt-4 pb-4 flex flex-col h-full">

            {/* Header row */}
            <div className="flex items-center justify-between mb-6">
              <h1
                onClick={handleNewChat}
                className="text-xl font-bold text-warm-text cursor-pointer hover:text-warm-text/70 transition-colors"
                title="Start new chat"
              >
                Chatbot AI
              </h1>
              <div className="flex items-center gap-1 pr-2">
                {/* Collapse button — desktop only */}
                <button
                  onClick={() => setSidebarCollapsed(true)}
                  className="hidden md:flex p-1.5 rounded-lg text-warm-muted hover:bg-[#242321] hover:text-warm-text transition-colors"
                  title="Collapse sidebar"
                >
                  <PanelLeft size={16} />
                </button>
                {/* Close button — mobile only */}
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="md:hidden p-1 hover:bg-warm-surface rounded"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* New Chat button */}
            <button
              onClick={handleNewChat}
              className="flex items-center justify-center gap-2 w-full py-3 px-4 bg-warm-text hover:bg-white rounded-xl transition-colors font-medium mb-6 shadow-lg text-[#1e1d1b]"
            >
              <Plus size={20} />
              New Chat
            </button>

            {/* Thread history */}
            <SidebarHistory
              threads={threads}
              activeThreadId={chatId}
              onSelect={handleSelectThread}
              onDelete={handleDeleteThread}
              onPin={pinThread}
              onRename={renameThread}
            />
          </div>
        )}
      </div>

      {/* ── Main Chat Area ───────────────────────────────────────────── */}
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

      {/* ── Global store error toast ─────────────────────────────────── */}
      {storeError && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] px-4 w-full max-w-md">
          <div className="flex items-center justify-between gap-3 bg-red-900/90 text-red-100 px-4 py-3 rounded-xl text-sm border border-red-700/60 shadow-2xl backdrop-blur">
            <span>⚠️ {storeError}</span>
            <button
              onClick={clearError}
              className="text-red-300 hover:text-white transition-colors shrink-0 font-bold"
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
