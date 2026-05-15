import React, { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';
import { MoreHorizontal, Pin, PinOff, Pencil, Trash2, Check, X } from 'lucide-react';

export function SidebarHistory({ threads, activeThreadId, onSelect, onDelete, onPin, onRename }) {
  const [openMenuId, setOpenMenuId] = useState(null);
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const menuRef = useRef(null);
  const renameInputRef = useRef(null);

  // Close dropdown when clicking outside of it
  useEffect(() => {
    if (!openMenuId) return;
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpenMenuId(null);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [openMenuId]);

  // Auto-focus the rename input when it appears
  useEffect(() => {
    if (renamingId && renameInputRef.current) {
      renameInputRef.current.focus();
      renameInputRef.current.select();
    }
  }, [renamingId]);

  const handleMenuToggle = (e, id) => {
    e.stopPropagation();
    setOpenMenuId((prev) => (prev === id ? null : id));
  };

  const handlePin = (e, thread) => {
    e.stopPropagation();
    setOpenMenuId(null);
    onPin(thread.id, !thread.is_pinned);
  };

  const handleStartRename = (e, thread) => {
    e.stopPropagation();
    setOpenMenuId(null);
    setRenamingId(thread.id);
    setRenameValue(thread.title);
  };

  const handleDelete = (e, threadId) => {
    e.stopPropagation();
    setOpenMenuId(null);
    onDelete(threadId);
  };

  const commitRename = (threadId) => {
    const trimmed = renameValue.trim();
    if (trimmed) onRename(threadId, trimmed);
    setRenamingId(null);
    setRenameValue('');
  };

  const cancelRename = () => {
    setRenamingId(null);
    setRenameValue('');
  };

  if (!threads || threads.length === 0) {
    return <div className="text-xs text-warm-muted px-2 italic mt-4">No recent chats</div>;
  }

  const pinned = threads.filter((t) => t.is_pinned);
  const history = threads.filter((t) => !t.is_pinned);

  const renderThread = (thread) => {
    const isActive = activeThreadId === thread.id;
    const isRenaming = renamingId === thread.id;
    const isMenuOpen = openMenuId === thread.id;

    return (
      <div
        key={thread.id}
        className={clsx(
          'relative w-full px-2 py-1.5 rounded-md text-xs transition-all duration-150 flex items-center gap-2',
          isActive
            ? 'bg-[#242321] text-warm-text'
            : 'text-warm-text/60 hover:bg-[#242321] hover:text-warm-text',
          'group'
        )}
      >
        {isRenaming ? (
          /* ── Inline rename input ── */
          <div className="flex items-center gap-1 flex-1 min-w-0">
            <input
              ref={renameInputRef}
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') commitRename(thread.id);
                if (e.key === 'Escape') cancelRename();
              }}
              onClick={(e) => e.stopPropagation()}
              className="flex-1 min-w-0 bg-[#171615] border border-[#373636] rounded px-1.5 py-0.5 text-warm-text text-xs focus:outline-none focus:border-warm-muted"
            />
            <button
              onClick={(e) => { e.stopPropagation(); commitRename(thread.id); }}
              className="p-0.5 hover:text-green-400 transition-colors shrink-0"
              title="Save"
            >
              <Check size={11} />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); cancelRename(); }}
              className="p-0.5 hover:text-red-400 transition-colors shrink-0"
              title="Cancel"
            >
              <X size={11} />
            </button>
          </div>
        ) : (
          <>
            {/* Thread title button */}
            <button
              type="button"
              onClick={() => onSelect(thread.id)}
              className="flex items-center min-w-0 flex-1 text-left gap-1.5"
              title={thread.title}
            >
              {thread.is_pinned && <Pin size={10} className="shrink-0 text-warm-muted" />}
              <span className="truncate">{thread.title}</span>
            </button>

            {/* ⋯ menu button */}
            <div
              className="relative shrink-0"
              ref={isMenuOpen ? menuRef : null}
            >
              <button
                type="button"
                onClick={(e) => handleMenuToggle(e, thread.id)}
                className={clsx(
                  'p-0.5 rounded transition-all',
                  isMenuOpen
                    ? 'opacity-100 text-warm-text'
                    : 'opacity-100 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100 text-warm-muted hover:text-warm-text'
                )}
                title="Options"
              >
                <MoreHorizontal size={13} />
              </button>

              {/* Dropdown */}
              {isMenuOpen && (
                <div className="absolute right-0 top-full mt-0.5 z-50 bg-[#242321] border border-[#373636] rounded-lg shadow-xl py-1 min-w-[130px]">
                  <button
                    onClick={(e) => handlePin(e, thread)}
                    className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-warm-text/80 hover:bg-[#2e2d2b] hover:text-warm-text transition-colors"
                  >
                    {thread.is_pinned ? <PinOff size={11} /> : <Pin size={11} />}
                    {thread.is_pinned ? 'Unpin' : 'Pin'}
                  </button>
                  <button
                    onClick={(e) => handleStartRename(e, thread)}
                    className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-warm-text/80 hover:bg-[#2e2d2b] hover:text-warm-text transition-colors"
                  >
                    <Pencil size={11} />
                    Rename
                  </button>
                  <div className="h-px bg-[#373636] my-1" />
                  <button
                    onClick={(e) => handleDelete(e, thread.id)}
                    className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-red-400/80 hover:bg-[#2e2d2b] hover:text-red-400 transition-colors"
                  >
                    <Trash2 size={11} />
                    Delete
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700">
      {pinned.length > 0 && (
        <>
          <div className="text-xs font-semibold text-warm-muted uppercase tracking-wider mb-1 px-2 mt-4">
            Pinned
          </div>
          {pinned.map(renderThread)}
        </>
      )}
      {history.length > 0 && (
        <>
          <div className="text-xs font-semibold text-warm-muted uppercase tracking-wider mb-1 px-2 mt-4">
            History
          </div>
          {history.map(renderThread)}
        </>
      )}
    </div>
  );
}
