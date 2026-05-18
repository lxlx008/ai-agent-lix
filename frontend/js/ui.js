class UI {
    static generateThreadId() {
        return 'thread_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    static escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static formatDate(timestamp) {
        if (!timestamp) return '刚刚';
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return '刚刚';
        if (minutes < 60) return `${minutes}分钟前`;
        if (hours < 24) return `${hours}小时前`;
        if (days < 7) return `${days}天前`;
        return date.toLocaleDateString('zh-CN');
    }

    static showWelcomeScreen() {
        const container = document.getElementById('messages-container');
        container.innerHTML = `
            <div class="welcome-screen">
                <div class="welcome-content">
                    <div class="welcome-icon">
                        <span class="material-icons">smart_toy</span>
                    </div>
                    <h3 class="welcome-title">你好呀！我是你的 AI 私人助手</h3>
                    <p class="welcome-subtitle">很高兴为你服务！请问有什么我可以帮助你的吗？</p>
                    <div class="welcome-features">
                        <p>💡 我可以帮你解答问题、提供建议</p>
                        <p>🔍 搜索最新信息和资讯</p>
                        <p>📝 提供创意和灵感</p>
                        <p>💬 陪你聊天交流</p>
                    </div>
                </div>
            </div>
        `;
    }

    static renderThreads(threads, currentThreadId, onNewThread, onSwitchThread, onDeleteThread) {
        const threadsList = document.getElementById('threads-list');
        threadsList.innerHTML = '';
        
        // 新对话按钮
        const newThreadItem = document.createElement('div');
        newThreadItem.className = 'thread-item new-thread';
        newThreadItem.innerHTML = `
            <div class="thread-icon new">
                <span class="material-icons">add</span>
            </div>
            <div class="thread-info">
                <div class="thread-title">新对话</div>
                <div class="thread-time">开始新的会话</div>
            </div>
        `;
        newThreadItem.addEventListener('click', onNewThread);
        threadsList.appendChild(newThreadItem);

        // 分割线
        const divider = document.createElement('div');
        divider.className = 'divider';
        threadsList.appendChild(divider);

        // 历史会话
        threads.forEach(thread => {
            const threadItem = document.createElement('div');
            threadItem.className = `thread-item ${thread.thread_id === currentThreadId ? 'active' : ''}`;
            threadItem.innerHTML = `
                <div class="thread-icon message">
                    <span class="material-icons">message</span>
                </div>
                <div class="thread-info">
                    <div class="thread-title">${this.escapeHtml(thread.title)}</div>
                    <div class="thread-time">${this.formatDate(thread.created_at)}</div>
                </div>
                <button class="delete-thread-btn" data-thread-id="${thread.thread_id}" title="删除会话">
                    <span class="material-icons">delete</span>
                </button>
            `;
            
            threadItem.addEventListener('click', (e) => {
                if (!e.target.closest('.delete-thread-btn')) {
                    onSwitchThread(thread.thread_id, thread.title);
                }
            });
            
            threadItem.querySelector('.delete-thread-btn').addEventListener('click', () => {
                onDeleteThread(thread.thread_id);
            });
            
            threadsList.appendChild(threadItem);
        });
    }

    static addMessage(role, content, scroll = true) {
        const container = document.getElementById('messages-container');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.innerHTML = `
            <div class="message-avatar ${role}">
                <span class="material-icons">${role === 'user' ? 'person' : 'smart_toy'}</span>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <p>${this.escapeHtml(content)}</p>
                </div>
            </div>
        `;
        container.appendChild(messageDiv);
        
        if (scroll) {
            container.scrollTop = container.scrollHeight;
        }
        
        return messageDiv;
    }

    static createAIMessageContainer() {
        const container = document.getElementById('messages-container');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `
            <div class="message-avatar assistant">
                <span class="material-icons">smart_toy</span>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <p class="ai-response-text"></p>
                    <div class="loading-dots">
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
        
        return {
            container: messageDiv,
            textElement: messageDiv.querySelector('.ai-response-text'),
            loadingElement: messageDiv.querySelector('.loading-dots')
        };
    }

    static clearMessages() {
        document.getElementById('messages-container').innerHTML = '';
    }

    static updateThreadTitle(title) {
        document.getElementById('current-thread-title').textContent = title;
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = UI;
}