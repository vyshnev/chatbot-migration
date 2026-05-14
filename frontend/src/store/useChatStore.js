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
      return true; // Return success status for components to react (e.g. redirect if active)
    } catch (err) {
      set({ error: err.message || 'Failed to delete thread' });
      return false;
    }
  }
}));
