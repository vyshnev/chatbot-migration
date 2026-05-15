import React from 'react';
import { Wrench, ExternalLink } from 'lucide-react';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const TOOL_NAME_MAP = {
  search_tool: "Web Search",
  calculator: "Calculator",
  get_stock_price: "Stock Price",
  update_memory: "Memory Updated",
  forget_memory: "Memory Deleted",
  get_all_memories: "Memory Read",
  save_memory: "Memory Saved",
  read_webpage: "Webpage Reader"
};

// ---------------------------------------------------------------------------
// Source parsing helpers
// ---------------------------------------------------------------------------

/**
 * Split message content into { body, sources }.
 * Works incrementally during streaming:
 *   - Once "Sources:" appears, it's stripped from body immediately (no flicker).
 *   - Chips appear one-by-one as each [label](url) pair completes.
 */
function parseSources(content) {
  // Match **Sources:** or Sources: (with or without bold markers, case-insensitive)
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

/** Extract a short readable label from a URL (e.g. "CNN" from edition.cnn.com). */
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
// SourcesBar — chip row rendered below the assistant message
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
// ToolMessage — collapsible tool call accordion
// ---------------------------------------------------------------------------
function ToolMessage({ msg }) {
  const [isOpen, setIsOpen] = React.useState(false);
  const friendlyName = TOOL_NAME_MAP[msg.name] || msg.name || "Tool Output";

  return (
    <div className="flex w-full justify-start">
      <div
        className="flex flex-col overflow-hidden bg-warm-surface/60 text-warm-muted rounded-lg text-sm border border-warm-surface cursor-pointer select-none max-w-[85%] shadow-sm"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2 px-3 py-1.5 hover:bg-warm-surface/80 transition-colors">
          <Wrench size={14} className="text-warm-muted shrink-0" />
          <span className="font-medium text-warm-text/80">{friendlyName}</span>
          <span
            className="ml-1 text-[10px] transform transition-transform duration-200"
            style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
          >
            ▽
          </span>
        </div>
        {isOpen && (
          <div
            className="px-3 pb-2 pt-1 border-t border-warm-surface/50 text-xs font-mono text-warm-muted/80 whitespace-pre-wrap break-words overflow-y-auto max-h-48 cursor-text"
            onClick={(e) => e.stopPropagation()}
          >
            {msg.content}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// MessageList
// ---------------------------------------------------------------------------
export function MessageList({ messages, messagesEndRef }) {
  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700">
      {/* Constrained column — same max-width as the input bar */}
      <div className="max-w-3xl mx-auto w-full px-4 py-4 md:py-6 space-y-6">
        {messages.map((msg) => {
          if (msg.role === 'tool') {
            return <ToolMessage key={msg.id} msg={msg} />;
          }

          const isUser = msg.role === 'user';

          if (isUser) {
            return (
              <div key={msg.id} className="flex w-full justify-end">
                <div className="max-w-[85%] rounded-2xl px-5 py-3.5 shadow-sm bg-[#1e1d1b] text-warm-text border border-[#373636] rounded-br-sm">
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            );
          }

          // Assistant message — parse sources out before rendering
          const { body, sources } = parseSources(msg.content);

          return (
            <div key={msg.id} className="flex w-full justify-start">
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
                        // Keep target="_blank" for any inline links in the body
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

                {/* Source chips — shown once at least one link is parsed */}
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
