import React, { useRef, useEffect } from 'react';
import { Send, Square } from 'lucide-react';

export function ChatInput({ input, setInput, onSubmit, onAbort, isLoading }) {
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
    <form onSubmit={onSubmit} className="w-full relative flex items-end gap-2 shadow-2xl bg-warm-surface border border-[#373636] rounded-2xl p-2 transition-all">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything"
        className="flex-1 bg-transparent text-warm-text py-2.5 px-4 focus:outline-none placeholder-warm-muted text-base resize-none overflow-y-auto max-h-[200px]"
        rows="1"
        disabled={isLoading}
        autoFocus
      />
      {isLoading ? (
        <button
          type="button"
          onClick={onAbort}
          className="p-3 bg-warm-muted hover:bg-warm-text rounded-xl text-matte-black transition-all shadow-lg mb-0.5 mr-0.5"
          title="Stop response"
        >
          <Square size={20} />
        </button>
      ) : (
        <button
          type="submit"
          disabled={!input.trim()}
          className="p-3 bg-warm-text hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-[#1e1d1b] transition-all shadow-lg mb-0.5 mr-0.5"
          title="Send message"
        >
          <Send size={20} />
        </button>
      )}
    </form>
  );
}
