import { useReducer, useCallback, useRef } from 'react';
import { chatService } from '../services/chatService';
import { useChatStore } from '../store/useChatStore';

export const initialState = {
  status: 'IDLE', // IDLE | STREAMING | SUCCESS | ERROR | ABORTED
  messages: [],
  error: null,
};

function removeEmptyAssistantPlaceholder(messages) {
  const lastMessage = messages[messages.length - 1];
  if (lastMessage?.role === 'assistant' && lastMessage.content === '') {
    return messages.slice(0, -1);
  }
  return messages;
}

export function streamReducer(state, action) {
  switch (action.type) {
    case 'SET_INITIAL_MESSAGES':
      return {
        ...state,
        status: 'SUCCESS',
        // Stamp a stable id on each message loaded from history so MessageList
        // can use key={msg.id} instead of key={index}.
        messages: action.payload.map((msg) => ({ ...msg, id: crypto.randomUUID() })),
        error: null,
      };
    case 'START_STREAM':
      return {
        ...state,
        status: 'STREAMING',
        error: null,
        messages: [
          ...state.messages,
          { role: 'user', content: action.payload, id: crypto.randomUUID() },
          { role: 'assistant', content: '', id: crypto.randomUUID() }, // Placeholder for streaming response
        ]
      };
    case 'APPEND_TOKEN': {
      const lastMsgIndex = state.messages.length - 1;
      const lastMsg = { ...state.messages[lastMsgIndex] };
      lastMsg.content += action.payload;
      
      const newMessages = [...state.messages];
      newMessages[lastMsgIndex] = lastMsg;
      
      return { ...state, messages: newMessages };
    }
    case 'STREAM_COMPLETE':
      return { ...state, status: 'SUCCESS' };
    case 'STREAM_ERROR':
      return {
        ...state,
        status: 'ERROR',
        error: action.payload,
        messages: removeEmptyAssistantPlaceholder(state.messages),
      };
    case 'ABORT_STREAM':
      return {
        ...state,
        status: 'ABORTED',
        messages: removeEmptyAssistantPlaceholder(state.messages),
      };
    case 'RESET_STREAM':
      return { ...initialState };
    default:
      return state;
  }
}

export function useChatStream() {
  const [state, dispatch] = useReducer(streamReducer, initialState);
  const loadThreads = useChatStore((store) => store.loadThreads);
  const abortControllerRef = useRef(null);

  const sendMessage = useCallback(async (content, currentThreadId, onNewThreadCreated) => {
    if (!content.trim() || state.status === 'STREAMING') return;

    dispatch({ type: 'START_STREAM', payload: content });

    let newThreadId = null;
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      await chatService.streamChat(
        content,
        currentThreadId,
        (chunk) => {
          dispatch({ type: 'APPEND_TOKEN', payload: chunk });
        },
        () => {
          dispatch({ type: 'STREAM_COMPLETE' });
          
          if (!currentThreadId && newThreadId) {
            // We just created a new thread, bubble the ID up so the URL can be updated
            if (onNewThreadCreated) onNewThreadCreated(newThreadId);
          }
          
          // Refresh the sidebar to show the new chat or updated title
          loadThreads();
        },
        (errorMsg) => {
          dispatch({ type: 'STREAM_ERROR', payload: errorMsg });
        },
        (id) => {
          newThreadId = id;
        },
        { signal: controller.signal }
      );
    } catch (err) {
      dispatch({ type: 'STREAM_ERROR', payload: err.message });
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
    }
  }, [state.status, loadThreads]);

  const setInitialMessages = useCallback((messages) => {
    dispatch({ type: 'SET_INITIAL_MESSAGES', payload: messages });
  }, []);

  const resetStream = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    dispatch({ type: 'RESET_STREAM' });
  }, []);

  const abortStream = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    dispatch({ type: 'ABORT_STREAM' });
  }, []);

  return {
    ...state,
    sendMessage,
    setInitialMessages,
    resetStream,
    abortStream
  };
}
