import apiClient from '../lib/axios';

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const chatService = {
    getThreads: async () => {
        const response = await apiClient.get('/threads');
        return response.data;
    },

    getHistory: async (threadId) => {
        const response = await apiClient.get(`/history/${threadId}`);
        return response.data;
    },

    deleteThread: async (threadId) => {
        const response = await apiClient.delete(`/threads/${threadId}`);
        return response.data;
    },

    // Streaming uses native fetch so we can read newline-delimited JSON incrementally.
    streamChat: async (
        message,
        threadId,
        onChunk,
        onComplete,
        onError,
        onThreadId,
        { signal } = {}
    ) => {
        try {
            const response = await fetch(`${baseURL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message, thread_id: threadId }),
                signal,
            });

            if (!response.ok) throw new Error('Failed to send message');
            if (!response.body) throw new Error('Response body is not readable');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let streamFailed = false;

            const processLine = (line) => {
                if (!line.trim() || streamFailed) return true;

                let data;
                try {
                    data = JSON.parse(line);
                } catch (error) {
                    console.error('Error parsing JSON stream event', error);
                    streamFailed = true;
                    onError('Received malformed stream data');
                    return false;
                }

                if (data.type === 'chunk') {
                    onChunk(data.content);
                } else if (data.type === 'thread_id') {
                    if (onThreadId) onThreadId(data.content);
                } else if (data.type === 'error') {
                    streamFailed = true;
                    onError(data.content || 'Stream failed');
                    return false;
                }

                return true;
            };

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep the last incomplete line in buffer

                for (const line of lines) {
                    if (!processLine(line)) return;
                }
            }

            buffer += decoder.decode();
            if (buffer.trim() && !processLine(buffer)) return;

            if (streamFailed) return;
            onComplete();
        } catch (error) {
            if (error.name === 'AbortError') return;
            onError(error.message);
        }
    }
};
