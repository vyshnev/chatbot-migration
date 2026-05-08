import React from 'react';
import clsx from 'clsx';
import { Trash2 } from 'lucide-react';

export function SidebarHistory({ threads, activeThreadId, onSelect, onDelete }) {
  if (!threads || threads.length === 0) {
    return <div className="text-sm text-warm-muted px-2 italic mt-4">No recent chats</div>;
  }

  return (
    <div className="flex-1 overflow-y-auto space-y-2 pr-2 scrollbar-thin scrollbar-thumb-gray-700">
      <div className="text-xs font-semibold text-warm-muted uppercase tracking-wider mb-2 px-2 mt-4">History</div>
      {threads.map(thread => (
        <button
          key={thread.id}
          onClick={() => onSelect(thread.id)}
          className={clsx(
            "w-full text-left p-3 rounded-lg text-sm transition-all duration-200 flex items-center gap-3 truncate",
            activeThreadId === thread.id
              ? "bg-warm-surface text-warm-text shadow-sm border border-warm-surface/80"
              : "text-warm-text/60 hover:bg-warm-surface hover:text-warm-text",
            "group"
          )}
        >
          <div className="flex items-center min-w-0 flex-1">
            <span className="truncate">{thread.title}</span>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(thread.id);
            }}
            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 hover:text-red-400 rounded transition-all"
            title="Delete chat"
          >
            <Trash2 size={14} />
          </button>
        </button>
      ))}
    </div>
  );
}
