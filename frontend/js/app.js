class App {
    constructor() {
        this.currentThreadId = null;
        this.currentThreadTitle = '新对话';
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadThreads();
        
        // 页面加载时检查历史会话
        const threads = Storage.getThreads();
        if (threads.length > 0) {
            const latestThread = threads.reduce((latest, t) => 
                t.updated_at > latest.updated_at ? t : latest
            );
            this.switchThread(latestThread.thread_id, latestThread.title);
        } else {
            this.createNewThread();
        }
    }

    bindEvents() {
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const newChatBtn = document.getElementById('new-chat-btn');
        const clearChatBtn = document.getElementById('clear-chat-btn');
        const uploadBtn = document.getElementById('upload-btn');
        const fileInput = document.getElementById('file-input');

        messageInput.addEventListener('input', () => {
            sendBtn.disabled = !messageInput.value.trim();
        });

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        sendBtn.addEventListener('click', () => this.sendMessage());
        newChatBtn.addEventListener('click', () => this.createNewThread());
        
        clearChatBtn.addEventListener('click', () => {
            if (this.currentThreadId && confirm('确定要清空当前会话吗？')) {
                API.deleteThread(this.currentThreadId).then(() => {
                    Storage.deleteThread(this.currentThreadId);
                    this.createNewThread();
                });
            }
        });

        uploadBtn.addEventListener('click', () => fileInput.click());
        
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                console.log('选择的文件:', file.name);
            }
        });
    }

    createNewThread() {
        this.currentThreadId = UI.generateThreadId();
        this.currentThreadTitle = '新对话';
        UI.updateThreadTitle('新对话');
        UI.showWelcomeScreen();
        document.getElementById('message-input').value = '';
        document.getElementById('send-btn').disabled = true;
        this.loadThreads();
    }

    async switchThread(threadId, title) {
        this.currentThreadId = threadId;
        this.currentThreadTitle = title;
        UI.updateThreadTitle(title);
        
        try {
            const messages = await API.getMessages(threadId);
            UI.clearMessages();
            
            if (messages.length === 0) {
                UI.showWelcomeScreen();
            } else {
                messages.forEach(msg => {
                    UI.addMessage(msg.role, msg.content, false);
                });
            }
        } catch (error) {
            console.error('加载历史消息失败:', error);
            UI.showWelcomeScreen();
        }
        
        this.loadThreads();
    }

    async deleteThread(threadId) {
        if (!confirm('确定要删除这个会话吗？')) return;
        
        try {
            await API.deleteThread(threadId);
            Storage.deleteThread(threadId);
            
            if (this.currentThreadId === threadId) {
                this.createNewThread();
            } else {
                this.loadThreads();
            }
        } catch (error) {
            console.error('删除会话失败:', error);
        }
    }

    loadThreads() {
        const threads = Storage.getThreads();
        UI.renderThreads(
            threads,
            this.currentThreadId,
            () => this.createNewThread(),
            (threadId, title) => this.switchThread(threadId, title),
            (threadId) => this.deleteThread(threadId)
        );
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message || !this.currentThreadId) return;

        UI.addMessage('user', message);
        messageInput.value = '';
        document.getElementById('send-btn').disabled = true;

        const aiMessage = UI.createAIMessageContainer();
        const { textElement, loadingElement } = aiMessage;

        try {
            const stream = await API.sendMessage(message, this.currentThreadId);
            const reader = stream.getReader();
            const decoder = new TextDecoder('utf-8');
            let responseText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                responseText += decoder.decode(value, { stream: true });
                textElement.textContent = responseText;
                document.getElementById('messages-container').scrollTop = 
                    document.getElementById('messages-container').scrollHeight;
            }

            loadingElement.remove();
            
            // 保存会话
            const threads = Storage.getThreads();
            const existingThread = threads.find(t => t.thread_id === this.currentThreadId);
            
            if (!existingThread) {
                const title = message.length > 30 ? message.substring(0, 30) + '...' : message;
                this.currentThreadTitle = title;
                UI.updateThreadTitle(title);
                Storage.saveThread(this.currentThreadId, title);
            } else {
                Storage.saveThread(this.currentThreadId, this.currentThreadTitle);
            }
            
            this.loadThreads();
        } catch (error) {
            console.error('发送消息失败:', error);
            textElement.textContent = '抱歉，发生了错误，请重试。';
            loadingElement.remove();
        }
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});