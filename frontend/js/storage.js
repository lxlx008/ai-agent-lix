const STORAGE_KEY = 'chat_threads';

class Storage {
    static getThreads() {
        try {
            const data = localStorage.getItem(STORAGE_KEY);
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('读取会话列表失败:', error);
            return [];
        }
    }

    static saveThread(threadId, title) {
        if (!threadId || !title) return;
        
        try {
            let threads = this.getThreads();
            const existingIndex = threads.findIndex(t => t.thread_id === threadId);
            const now = Date.now();
            
            if (existingIndex >= 0) {
                threads[existingIndex].title = title;
                threads[existingIndex].updated_at = now;
            } else {
                threads.unshift({
                    thread_id: threadId,
                    title: title,
                    created_at: now,
                    updated_at: now
                });
            }
            
            localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
        } catch (error) {
            console.error('保存会话失败:', error);
        }
    }

    static deleteThread(threadId) {
        try {
            let threads = this.getThreads();
            threads = threads.filter(t => t.thread_id !== threadId);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
        } catch (error) {
            console.error('删除会话失败:', error);
        }
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = Storage;
}