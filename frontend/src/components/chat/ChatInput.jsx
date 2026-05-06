import React, { useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

export function ChatInput({ input, setInput, onSubmit, isLoading }) {
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isLoading) onSubmit(e);
    }
  };

  return (
    <form onSubmit={onSubmit} className="w-full relative flex items-end gap-2 shadow-2xl bg-gray-800/80 border border-gray-700 rounded-2xl p-2 transition-all">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
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
  );
}
