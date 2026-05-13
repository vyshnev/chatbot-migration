import { describe, it, expect } from 'vitest';
import { streamReducer, initialState } from '../hooks/useChatStream';

describe('useChatStream Reducer', () => {
  it('handles SET_INITIAL_MESSAGES', () => {
    const fakeMessages = [{ role: 'user', content: 'Hello' }];
    const nextState = streamReducer(initialState, {
      type: 'SET_INITIAL_MESSAGES',
      payload: fakeMessages,
    });
    
    expect(nextState.status).toBe('SUCCESS');
    expect(nextState.messages).toEqual(fakeMessages);
    expect(nextState.error).toBeNull();
  });

  it('handles START_STREAM by adding user message and empty assistant placeholder', () => {
    const nextState = streamReducer(initialState, {
      type: 'START_STREAM',
      payload: 'What is the capital of France?',
    });
    
    expect(nextState.status).toBe('STREAMING');
    expect(nextState.messages).toHaveLength(2);
    expect(nextState.messages[0]).toEqual({ role: 'user', content: 'What is the capital of France?' });
    expect(nextState.messages[1]).toEqual({ role: 'assistant', content: '' });
  });

  it('handles APPEND_TOKEN by building the string on the last message', () => {
    // Start with a state that has an empty placeholder
    const state = {
      ...initialState,
      status: 'STREAMING',
      messages: [{ role: 'assistant', content: 'Par' }]
    };
    
    const nextState = streamReducer(state, {
      type: 'APPEND_TOKEN',
      payload: 'is',
    });
    
    expect(nextState.messages[0].content).toBe('Paris');
  });

  it('handles STREAM_ERROR by removing empty placeholder and setting error', () => {
    const state = {
      ...initialState,
      status: 'STREAMING',
      messages: [
        { role: 'user', content: 'Hi' },
        { role: 'assistant', content: '' } // This should be removed on error
      ]
    };
    
    const nextState = streamReducer(state, {
      type: 'STREAM_ERROR',
      payload: 'Network failure',
    });
    
    expect(nextState.status).toBe('ERROR');
    expect(nextState.error).toBe('Network failure');
    expect(nextState.messages).toHaveLength(1); // The empty assistant placeholder is gone
  });
});
