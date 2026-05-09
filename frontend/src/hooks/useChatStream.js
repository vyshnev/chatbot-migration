import { useReducer, useCallback, useRef } from 'react';
import { chatService } from '../services/chatService';
import { useChatStore } from '../store/useChatStore';

const initialState = {
  status: 'IDLE', // IDLE | STREAMING | SUCCESS | ERROR | ABORTED
  messages: [],
  error: null,
};

function streamReducer(state, action) {
  switch (action.type) {
    case 'SET_INITIAL_MESSAGES':
      return { ...state, status: 'SUCCESS', messages: action.payload, error: null };
    case 'START_STREAM':
      return {
        ...state,
        status: 'STREAMING',
        error: null,
        messages: [
          ...state.messages,
          { role: 'user', content: action.payload },
          { role: 'assistant', content: '' } // Placeholder for streaming response
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
      return { ...state, status: 'ERROR', error: action.payload };
    case 'ABORT_STREAM':
      return { ...state, status: 'ABORTED' };
    case 'RESET_STREAM':
      return { ...initialState };
    default:
      return state;
  }
}

export function useChatStream() {
  const [state, dispatch] = useReducer(streamReducer, initialState);
  const loadThreads = useChatStore((store) => store.loadThreads);
  
  // Use a ref so the sendMessage function signature remains stable
  const threadIdRef = useRef(null);

  const sendMessage = useCallback(async (content, currentThreadId, onNewThreadCreated) => {
    if (!content.trim() || state.status === 'STREAMING') return;

    dispatch({ type: 'START_STREAM', payload: content });
    threadIdRef.current = currentThreadId;

    let newThreadId = null;

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
        }
      );
    } catch (err) {
      dispatch({ type: 'STREAM_ERROR', payload: err.message });
    }
  }, [state.status, loadThreads]);

  const setInitialMessages = useCallback((messages) => {
    dispatch({ type: 'SET_INITIAL_MESSAGES', payload: messages });
  }, []);

  const resetStream = useCallback(() => {
    dispatch({ type: 'RESET_STREAM' });
  }, []);

  const abortStream = useCallback(() => {
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
