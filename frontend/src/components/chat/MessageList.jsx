import React from 'react';
import { Wrench } from 'lucide-react';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function MessageList({ messages, messagesEndRef }) {
  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-thin scrollbar-thumb-gray-700">
      {messages.map((msg, idx) => {
        if (msg.role === 'tool') {
          return (
            <div key={idx} className="flex w-full justify-start pl-4 md:pl-12">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-800/50 text-gray-400 rounded-lg text-sm border border-gray-700/50">
                <Wrench size={14} className="text-gray-500" />
                <span className="font-mono">{msg.content}</span>
              </div>
            </div>
          );
        }

        const isUser = msg.role === 'user';
        return (
          <div key={idx} className={clsx("flex w-full", isUser ? "justify-end" : "justify-start")}>
            <div className={clsx(
              "max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-3.5 shadow-sm",
              isUser
                ? "bg-blue-600 text-white rounded-br-sm"
                : "bg-gray-800 border border-gray-700 text-gray-100 rounded-bl-sm shadow-xl"
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
  );
}
