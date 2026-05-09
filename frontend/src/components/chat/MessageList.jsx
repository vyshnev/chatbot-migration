import React from 'react';
import { Wrench } from 'lucide-react';
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
  save_memory: "Memory Saved"
};

function ToolMessage({ msg }) {
  const [isOpen, setIsOpen] = React.useState(false);
  const friendlyName = TOOL_NAME_MAP[msg.name] || msg.name || "Tool Output";

  return (
    <div className="flex w-full justify-start">
      <div className="flex flex-col overflow-hidden bg-warm-surface/60 text-warm-muted rounded-lg text-sm border border-warm-surface cursor-pointer select-none max-w-[85%] shadow-sm" onClick={() => setIsOpen(!isOpen)}>
        <div className="flex items-center gap-2 px-3 py-1.5 hover:bg-warm-surface/80 transition-colors">
          <Wrench size={14} className="text-warm-muted shrink-0" />
          <span className="font-medium text-warm-text/80">{friendlyName}</span>
          <span className="ml-1 text-[10px] transform transition-transform duration-200" style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}>
            ▽
          </span>
        </div>
        {isOpen && (
          <div className="px-3 pb-2 pt-1 border-t border-warm-surface/50 text-xs font-mono text-warm-muted/80 whitespace-pre-wrap break-words overflow-y-auto max-h-48 cursor-text" onClick={(e) => e.stopPropagation()}>
            {msg.content}
          </div>
        )}
      </div>
    </div>
  );
}

export function MessageList({ messages, messagesEndRef }) {
  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700">
      {/* Constrained column — same max-width as the input bar so all content
          aligns between the same two vertical rails */}
      <div className="max-w-3xl mx-auto w-full px-4 py-4 md:py-6 space-y-6">
        {messages.map((msg, idx) => {
          if (msg.role === 'tool') {
            return <ToolMessage key={idx} msg={msg} />;
          }

          const isUser = msg.role === 'user';
          return (
            <div key={idx} className={clsx("flex w-full", isUser ? "justify-end" : "justify-start")}>
              <div className={clsx(
                "max-w-[85%] rounded-2xl px-5 py-3.5 shadow-sm",
                isUser
                  ? "bg-blue-600 text-white rounded-br-sm"
                  : "bg-warm-surface border border-warm-surface/60 text-warm-text rounded-bl-sm shadow-xl"
              )}>
                {isUser ? (
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                ) : (
                  <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700">
                    {msg.content === '' ? (
                      <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse" />
                    ) : (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} className="h-px w-full" />
      </div>
    </div>
  );
}
