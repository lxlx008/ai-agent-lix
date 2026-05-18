class API {
    static async sendMessage(message, threadId) {
        const response = await fetch(`/api/v1/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                image_url: '',
                thread_id: threadId
            })
        });

        if (!response.ok) {
            throw new Error('请求失败');
        }

        return response.body;
    }

    static async getMessages(threadId) {
        const response = await fetch(`/api/v1/chat/messages?thread_id=${threadId}`);
        const data = await response.json();
        return data.messages || [];
    }

    static async getThreads() {
        try {
            const response = await fetch(`/api/v1/chat/threads`);
            const data = await response.json();
            return data.threads || [];
        } catch (error) {
            console.error('获取服务器会话列表失败:', error);
            return [];
        }
    }

    static async deleteThread(threadId) {
        await fetch(`/api/v1/chat/messages?thread_id=${threadId}`, {
            method: 'DELETE'
        });
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}