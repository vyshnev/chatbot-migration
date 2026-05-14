import React from 'react';
import clsx from 'clsx';
import { Trash2 } from 'lucide-react';

export function SidebarHistory({ threads, activeThreadId, onSelect, onDelete }) {
  if (!threads || threads.length === 0) {
    return <div className="text-xs text-warm-muted px-2 italic mt-4">No recent chats</div>;
  }

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700">
      <div className="text-xs font-semibold text-warm-muted uppercase tracking-wider mb-1 px-2 mt-4">History</div>
      {threads.map(thread => (
        <div
          key={thread.id}
          className={clsx(
            "w-full px-2 py-1.5 rounded-md text-xs transition-all duration-150 flex items-center gap-2",
            activeThreadId === thread.id
              ? "bg-warm-surface text-warm-text"
              : "text-warm-text/60 hover:bg-warm-surface/60 hover:text-warm-text",
            "group"
          )}
        >
          <button
            type="button"
            onClick={() => onSelect(thread.id)}
            className="flex items-center min-w-0 flex-1 text-left"
            title={thread.title}
          >
            <span className="truncate">{thread.title}</span>
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(thread.id);
            }}
            className="opacity-100 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100 p-0.5 hover:bg-red-500/20 hover:text-red-400 rounded transition-all shrink-0"
            title="Delete chat"
            aria-label={`Delete ${thread.title}`}
          >
            <Trash2 size={12} />
          </button>
        </div>
      ))}
    </div>
  );
}
