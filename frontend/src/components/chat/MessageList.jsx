import React from 'react';
import {
  Search, Globe, Hash, TrendingUp, Brain, Trash2, RefreshCw,
  Settings, ChevronDown, ExternalLink
} from 'lucide-react';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// ---------------------------------------------------------------------------
// Tool metadata — icon + friendly name + accent colour per tool
// ---------------------------------------------------------------------------
const TOOL_CONFIG = {
  search_tool:     { name: 'Web Search',      Icon: Search,     color: 'text-blue-400' },
  read_webpage:    { name: 'Webpage Reader',   Icon: Globe,      color: 'text-emerald-400' },
  calculator:      { name: 'Calculator',       Icon: Hash,       color: 'text-yellow-400' },
  get_stock_price: { name: 'Stock Price',      Icon: TrendingUp, color: 'text-green-400' },
  save_memory:     { name: 'Memory Saved',     Icon: Brain,      color: 'text-purple-400' },
  forget_memory:   { name: 'Memory Deleted',   Icon: Trash2,     color: 'text-red-400' },
  update_memory:   { name: 'Memory Updated',   Icon: RefreshCw,  color: 'text-purple-400' },
};

function getToolConfig(toolName) {
  return TOOL_CONFIG[toolName] || { name: toolName || 'Tool', Icon: Settings, color: 'text-warm-muted' };
}

/** Extract a short one-line context string from a tool's output. */
function getShortContext(msg) {
  const content = (msg.content || '').trim();
  if (msg.name === 'read_webpage') {
    // We prepend "Source: {url}" — extract just the hostname
    const match = content.match(/^Source:\s*(https?:\/\/[^\s\n]+)/i);
    if (match) {
      try { return new URL(match[1]).hostname.replace(/^www\./, ''); } catch { return match[1]; }
    }
  }
  // Default: first non-empty line, capped at 70 chars
  const first = content.split('\n').find(l => l.trim()) || '';
  return first.length > 70 ? first.slice(0, 70) + '…' : first;
}

// ---------------------------------------------------------------------------
// ToolGroup — single collapsible row for consecutive tool messages
// ---------------------------------------------------------------------------
function ToolGroup({ toolMessages }) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [expandedIdx, setExpandedIdx] = React.useState(null);

  // Build deduplicated summary: "Web Search · Webpage Reader ×2"
  const nameCounts = {};
  toolMessages.forEach(msg => {
    const name = getToolConfig(msg.name).name;
    nameCounts[name] = (nameCounts[name] || 0) + 1;
  });
  const summary = Object.entries(nameCounts)
    .map(([name, count]) => (count > 1 ? `${name} ×${count}` : name))
    .join(' · ');

  return (
    <div className="flex w-full justify-start">
      <div className="w-full max-w-xl">

        {/* ── Collapsed header ───────────────────────────────────────── */}
        <button
          type="button"
          onClick={() => setIsOpen(o => !o)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#2e2d2b] bg-[#1a1918] text-xs text-warm-muted hover:text-warm-text hover:border-[#373636] transition-all w-full text-left"
        >
          <Settings size={12} className="shrink-0" />
          <span className="font-medium text-warm-text/70">
            {toolMessages.length} {toolMessages.length === 1 ? 'step' : 'steps'}
          </span>
          <span className="text-warm-muted/50 truncate">· {summary}</span>
          <ChevronDown
            size={12}
            className={clsx(
              'shrink-0 ml-auto transition-transform duration-200',
              isOpen && 'rotate-180'
            )}
          />
        </button>

        {/* ── Expanded list ──────────────────────────────────────────── */}
        {isOpen && (
          <div className="mt-1.5 ml-2 border-l border-[#2e2d2b] pl-3 flex flex-col gap-0.5">
            {toolMessages.map((msg, idx) => {
              const { name: friendlyName, Icon, color } = getToolConfig(msg.name);
              const context = getShortContext(msg);
              const isRawOpen = expandedIdx === idx;

              return (
                <div key={msg.id} className="flex flex-col">
                  <button
                    type="button"
                    onClick={() => setExpandedIdx(isRawOpen ? null : idx)}
                    className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-[#242321] transition-colors text-left w-full group"
                  >
                    <Icon size={13} className={clsx('shrink-0', color)} />
                    <span className="text-xs font-medium text-warm-text/80 shrink-0">
                      {friendlyName}
                    </span>
                    {context && (
                      <span className="text-[11px] text-warm-muted/55 truncate">{context}</span>
                    )}
                    <ChevronDown
                      size={11}
                      className={clsx(
                        'shrink-0 ml-auto text-warm-muted/30 group-hover:text-warm-muted/60 transition-transform duration-150',
                        isRawOpen && 'rotate-180'
                      )}
                    />
                  </button>

                  {/* Raw output — secondary expand */}
                  {isRawOpen && (
                    <div className="mx-2 mb-1 px-3 py-2 rounded-md bg-[#171615] border border-[#2e2d2b] text-[11px] font-mono text-warm-muted/65 whitespace-pre-wrap break-words overflow-y-auto max-h-48">
                      {msg.content}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Source parsing helpers
// ---------------------------------------------------------------------------

/**
 * Split message content into { body, sources }.
 * Streaming-safe: strips "Sources:" from body the moment it appears,
 * then chips render progressively as each [label](url) completes.
 */
function parseSources(content) {
  const splitIdx = content.search(/\*?\*?Sources:\*?\*?\s*/im);
  if (splitIdx === -1) return { body: content, sources: [] };

  const body = content.slice(0, splitIdx).trim();
  const sourcesText = content.slice(splitIdx);

  const sources = [];
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  let m;
  while ((m = linkRegex.exec(sourcesText)) !== null) {
    sources.push({ label: m[1], url: m[2] });
  }

  return { body, sources };
}

function getDomain(url) {
  try {
    const hostname = new URL(url).hostname.replace(/^www\./, '');
    const root = hostname.split('.')[0];
    return root.charAt(0).toUpperCase() + root.slice(1);
  } catch {
    return url;
  }
}

// ---------------------------------------------------------------------------
// SourcesBar — chip row below assistant message
// ---------------------------------------------------------------------------
function SourcesBar({ sources }) {
  if (!sources.length) return null;
  return (
    <div className="mt-4 pt-3 border-t border-[#2e2d2b] flex flex-wrap items-center gap-2">
      <span className="text-[10px] font-medium text-warm-muted uppercase tracking-wider shrink-0 mr-1">
        Sources
      </span>
      {sources.map((src, i) => (
        <a
          key={i}
          href={src.url}
          target="_blank"
          rel="noopener noreferrer"
          title={src.url}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-[#373636] bg-[#1e1d1b] text-xs text-warm-text/60 hover:text-warm-text hover:border-[#555453] transition-all duration-150"
        >
          <ExternalLink size={10} className="shrink-0" />
          <span>{getDomain(src.url)}</span>
        </a>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Message grouping — collapse consecutive tool messages into one ToolGroup
// ---------------------------------------------------------------------------
function groupMessages(messages) {
  const groups = [];
  let i = 0;
  while (i < messages.length) {
    if (messages[i].role === 'tool') {
      const toolBatch = [];
      while (i < messages.length && messages[i].role === 'tool') {
        toolBatch.push(messages[i]);
        i++;
      }
      groups.push({ type: 'tool_group', messages: toolBatch, key: toolBatch[0].id });
    } else {
      groups.push({ type: messages[i].role, message: messages[i], key: messages[i].id });
      i++;
    }
  }
  return groups;
}

// ---------------------------------------------------------------------------
// MessageList
// ---------------------------------------------------------------------------
export function MessageList({ messages, messagesEndRef }) {
  const grouped = groupMessages(messages);

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700">
      {/* Constrained column — same max-width as the input bar */}
      <div className="max-w-3xl mx-auto w-full px-4 py-4 md:py-6 space-y-6">
        {grouped.map(group => {
          // ── Tool group ──────────────────────────────────────────────
          if (group.type === 'tool_group') {
            return <ToolGroup key={group.key} toolMessages={group.messages} />;
          }

          const msg = group.message;
          const isUser = group.type === 'user';

          // ── User message ────────────────────────────────────────────
          if (isUser) {
            return (
              <div key={group.key} className="flex w-full justify-end">
                <div className="max-w-[85%] rounded-2xl px-5 py-3.5 shadow-sm bg-[#1e1d1b] text-warm-text border border-[#373636] rounded-br-sm">
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            );
          }

          // ── Assistant message ───────────────────────────────────────
          const { body, sources } = parseSources(msg.content);

          return (
            <div key={group.key} className="flex w-full justify-start">
              <div className="w-full text-warm-text py-2">
                <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700">
                  {msg.content === '' ? (
                    /* Loading dots */
                    <span className="flex items-center gap-1.5 py-1">
                      {[0, 180, 360].map((delay) => (
                        <span
                          key={delay}
                          className="w-1.5 h-1.5 rounded-full bg-warm-muted animate-pulse"
                          style={{ animationDelay: `${delay}ms` }}
                        />
                      ))}
                    </span>
                  ) : (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        a: ({ node, ...props }) => (
                          <a
                            {...props}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-amber-400/90 hover:text-amber-300 underline underline-offset-2 transition-colors"
                          />
                        ),
                      }}
                    >
                      {body}
                    </ReactMarkdown>
                  )}
                </div>

                {/* Source chips */}
                <SourcesBar sources={sources} />
              </div>
            </div>
          );
        })}

        <div ref={messagesEndRef} className="h-px w-full" />
      </div>
    </div>
  );
}
