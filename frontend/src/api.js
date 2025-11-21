const API_BASE_URL = 'http://localhost:8000';

export const getThreads = async () => {
    const response = await fetch(`${API_BASE_URL}/threads`);
    if (!response.ok) throw new Error('Failed to fetch threads');
    return response.json();
};

export const getHistory = async (threadId) => {
    const response = await fetch(`${API_BASE_URL}/history/${threadId}`);
    if (!response.ok) throw new Error('Failed to fetch history');
    return response.json();
};

export const streamChat = async (message, threadId, onChunk, onComplete, onError, onThreadId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message, thread_id: threadId }),
        });

        if (!response.ok) throw new Error('Failed to send message');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep the last incomplete line in buffer

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);
                    if (data.type === 'chunk') {
                        onChunk(data.content);
                    } else if (data.type === 'thread_id') {
                        if (onThreadId) onThreadId(data.content);
                    } else if (data.type === 'error') {
                        onError(data.content);
                    }
                } catch (e) {
                    console.error('Error parsing JSON chunk', e);
                }
            }
        }
        onComplete();
    } catch (error) {
        onError(error.message);
    }
};
