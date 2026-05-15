import { create } from 'zustand';
import { chatService } from '../services/chatService';

export const useChatStore = create((set) => ({
  // State
  threads: [],
  isSidebarOpen: true,
  isThreadsLoading: false,
  error: null,

  // Actions
  setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  clearError: () => set({ error: null }),

  loadThreads: async () => {
    set({ isThreadsLoading: true, error: null });
    try {
      const data = await chatService.getThreads();
      set({ threads: data.threads, isThreadsLoading: false });
    } catch (err) {
      set({ error: err.message || 'Failed to load threads', isThreadsLoading: false });
    }
  },

  deleteThread: async (threadId) => {
    try {
      await chatService.deleteThread(threadId);
      // Optimistic UI update
      set((state) => ({
        threads: state.threads.filter((t) => t.id !== threadId)
      }));
      return true;
    } catch (err) {
      set({ error: err.message || 'Failed to delete thread' });
      return false;
    }
  },

  pinThread: async (threadId, pinned) => {
    try {
      await chatService.pinThread(threadId, pinned);
      // Optimistic update: flip the flag and re-sort (pinned first)
      set((state) => {
        const updated = state.threads.map((t) =>
          t.id === threadId ? { ...t, is_pinned: pinned } : t
        );
        // Stable sort: pinned first, preserve existing order within each group
        const pinnedThreads = updated.filter((t) => t.is_pinned);
        const historyThreads = updated.filter((t) => !t.is_pinned);
        return { threads: [...pinnedThreads, ...historyThreads] };
      });
      return true;
    } catch (err) {
      set({ error: err.message || 'Failed to update pin' });
      return false;
    }
  },

  renameThread: async (threadId, title) => {
    try {
      await chatService.renameThread(threadId, title);
      // Optimistic update
      set((state) => ({
        threads: state.threads.map((t) =>
          t.id === threadId ? { ...t, title } : t
        )
      }));
      return true;
    } catch (err) {
      set({ error: err.message || 'Failed to rename thread' });
      return false;
    }
  },
}));
