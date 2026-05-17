import React, { useRef, useEffect, useState } from 'react';
import { Send, Square, Paperclip, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import { chatService } from '../../services/chatService';

const MAX_FILE_SIZE_MB = 10;

/** Map backend status → UI feedback */
const UPLOAD_MESSAGES = {
  success:   null,                                        // handled by onUploadComplete
  duplicate: 'Already uploaded to this conversation.',
  error:     'Upload failed. Please try again.',
  toolarge:  `File exceeds the ${MAX_FILE_SIZE_MB} MB limit.`,
  wrongtype: 'Only PDF files are supported.',
};

export function ChatInput({ 
  input, 
  setInput, 
  onSubmit, 
  onAbort, 
  isLoading, 
  threadId, 
  onUploadComplete,
  pendingFile,
  onPendingFileSet
}) {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // 'idle' | 'uploading' | 'success' | 'duplicate' | 'error' | 'toolarge' | 'wrongtype'
  const [uploadStatus, setUploadStatus] = useState('idle');

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  // Auto-clear non-idle status after 3 s (except 'uploading')
  useEffect(() => {
    if (uploadStatus === 'idle' || uploadStatus === 'uploading') return;
    const timer = setTimeout(() => setUploadStatus('idle'), 3000);
    return () => clearTimeout(timer);
  }, [uploadStatus]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if ((input.trim() || pendingFile) && !isLoading) onSubmit(e);
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    // Reset so the same file can be re-selected after a failure
    e.target.value = '';

    // Client-side validation
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadStatus('wrongtype');
      return;
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setUploadStatus('toolarge');
      return;
    }

    // If no thread exists yet, stage the file instead of uploading
    if (!threadId) {
      if (onPendingFileSet) {
        onPendingFileSet(file);
      }
      return;
    }

    setUploadStatus('uploading');

    try {
      const data = await chatService.uploadFile(file, threadId);

      if (data.status === 'duplicate') {
        setUploadStatus('duplicate');
      } else {
        setUploadStatus('success');
        onUploadComplete?.();
      }
    } catch {
      setUploadStatus('error');
    }
  };

  const isUploading = uploadStatus === 'uploading';
  const canUpload   = !isLoading && !isUploading;
  const canSend     = (input.trim().length > 0 || pendingFile) && !isLoading;

  return (
    <div className="flex flex-col gap-0 w-full">
      {/* Upload feedback toast — shown above the form, auto-dismisses after 3 s */}
      {uploadStatus !== 'idle' && uploadStatus !== 'uploading' && uploadStatus !== 'success' && (
        <div className={clsx(
          'mb-2 px-3 py-1.5 rounded-lg text-xs flex items-center gap-2 border',
          uploadStatus === 'duplicate'
            ? 'bg-amber-900/30 border-amber-700/40 text-amber-300'
            : 'bg-red-900/30 border-red-700/40 text-red-300'
        )}>
          <AlertCircle size={12} className="shrink-0" />
          {UPLOAD_MESSAGES[uploadStatus]}
        </div>
      )}

      {/* Pending file chip — shown above the form when staged for a new thread */}
      {pendingFile && (
        <div className="mb-2 self-start px-3 py-1.5 rounded-lg text-xs flex items-center gap-2 border bg-[#1e1d1b] border-[#2e2d2b] text-warm-muted/90">
          <Paperclip size={12} className="shrink-0 text-emerald-400" />
          <span className="truncate max-w-[200px]">{pendingFile.name}</span>
          <button 
            type="button" 
            onClick={() => onPendingFileSet(null)}
            className="ml-auto text-warm-muted/50 hover:text-red-400 ml-2"
            title="Remove file"
          >
            ✕
          </button>
        </div>
      )}

      <form onSubmit={onSubmit} className="w-full relative flex items-end gap-2 shadow-2xl bg-warm-surface border border-[#373636] rounded-2xl p-2 transition-all">

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileSelect}
          disabled={!canUpload}
        />

        {/* Paperclip button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={!canUpload}
          title="Upload PDF"
          className={clsx(
            'p-2.5 rounded-xl transition-all mb-0.5 shrink-0',
            canUpload
              ? 'text-warm-muted hover:text-warm-text hover:bg-[#2e2d2b]'
              : 'text-warm-muted/30 cursor-not-allowed'
          )}
        >
          {isUploading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : uploadStatus === 'success' ? (
            <CheckCircle2 size={18} className="text-emerald-400" />
          ) : (
            <Paperclip size={18} />
          )}
        </button>

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
            disabled={!canSend}
            className="p-3 bg-warm-text hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-[#1e1d1b] transition-all shadow-lg mb-0.5 mr-0.5"
            title="Send message"
          >
            <Send size={20} />
          </button>
        )}
      </form>
    </div>
  );
}
