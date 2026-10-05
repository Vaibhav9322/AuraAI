/**
 * AuraAI Sidebar Controller - Conversations & Navigation
 */

class SidebarController {
    constructor() {
        this.sidebarEl = document.getElementById('sidebar');
        this.historyContainerEl = document.getElementById('history-container');
        this.searchInputEl = document.getElementById('sidebar-search');
        this.newChatBtnEl = document.getElementById('new-chat-btn');
        this.activeConversationId = null;
        this.searchDebounceTimer = null;

        this.init();
    }

    init() {
        if (this.newChatBtnEl) {
            this.newChatBtnEl.addEventListener('click', () => this.startNewChat());
        }

        if (this.searchInputEl) {
            this.searchInputEl.addEventListener('input', (e) => {
                clearTimeout(this.searchDebounceTimer);
                this.searchDebounceTimer = setTimeout(() => {
                    this.loadConversations(e.target.value.trim());
                }, 250);
            });
        }

        // Initial load
        this.loadConversations();
    }

    async loadConversations(searchQuery = '') {
        try {
            let url = '/api/conversations?grouped=true';
            if (searchQuery) {
                url += `&search=${encodeURIComponent(searchQuery)}`;
            }

            const response = await fetch(url);
            if (!response.ok) return;

            const data = await response.json();
            this.renderGroupedHistory(data);
        } catch (err) {
            console.error("Failed to load conversations:", err);
        }
    }

    renderGroupedHistory(grouped) {
        if (!this.historyContainerEl) return;
        this.historyContainerEl.innerHTML = '';

        const sections = [
            { key: 'today', title: 'Today' },
            { key: 'yesterday', title: 'Yesterday' },
            { key: 'previous_7_days', title: 'Previous 7 Days' },
            { key: 'older', title: 'Older' }
        ];

        let totalCount = 0;

        sections.forEach(sec => {
            const items = grouped[sec.key] || [];
            if (items.length === 0) return;

            totalCount += items.length;

            const sectionEl = document.createElement('div');
            sectionEl.className = 'history-section';

            const titleEl = document.createElement('div');
            titleEl.className = 'history-group-title';
            titleEl.textContent = sec.title;

            const listEl = document.createElement('ul');
            listEl.className = 'history-list';

            items.forEach(conv => {
                const itemEl = document.createElement('li');
                itemEl.className = `history-item ${conv.id === this.activeConversationId ? 'active' : ''}`;
                itemEl.dataset.id = conv.id;

                itemEl.innerHTML = `
                    <span class="history-item-title">${this.escapeHtml(conv.title)}</span>
                    <div class="history-item-actions">
                        <button class="action-icon-btn btn-rename" title="Rename">✎</button>
                        <button class="action-icon-btn btn-delete" title="Delete">✕</button>
                    </div>
                `;

                // Item click -> select conversation
                itemEl.addEventListener('click', (e) => {
                    if (e.target.classList.contains('action-icon-btn')) return;
                    this.selectConversation(conv.id);
                });

                // Rename action
                itemEl.querySelector('.btn-rename').addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.renameConversation(conv.id, conv.title);
                });

                // Delete action
                itemEl.querySelector('.btn-delete').addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteConversation(conv.id);
                });

                listEl.appendChild(itemEl);
            });

            sectionEl.appendChild(titleEl);
            sectionEl.appendChild(listEl);
            this.historyContainerEl.appendChild(sectionEl);
        });

        if (totalCount === 0) {
            this.historyContainerEl.innerHTML = `
                <div style="font-size: var(--font-size-xs); color: var(--text-muted); padding: var(--space-4); text-align: center;">
                    No conversations yet
                </div>
            `;
        }
    }

    selectConversation(conversationId) {
        this.activeConversationId = conversationId;
        
        // Update active class in sidebar
        document.querySelectorAll('.history-item').forEach(el => {
            if (el.dataset.id === conversationId) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });

        // Trigger global chat load event
        if (window.chatController) {
            window.chatController.loadConversationMessages(conversationId);
        }
    }

    startNewChat() {
        this.activeConversationId = null;
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
        if (window.chatController) {
            window.chatController.resetToWelcomeScreen();
        }
    }

    async renameConversation(conversationId, currentTitle) {
        const newTitle = prompt("Enter new title for this conversation:", currentTitle);
        if (!newTitle || newTitle.trim() === '' || newTitle === currentTitle) return;

        try {
            const res = await fetch(`/api/conversations/${conversationId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle.trim() })
            });

            if (res.ok) {
                this.loadConversations();
            }
        } catch (err) {
            console.error("Failed to rename conversation:", err);
        }
    }

    async deleteConversation(conversationId) {
        if (!confirm("Are you sure you want to delete this conversation?")) return;

        try {
            const res = await fetch(`/api/conversations/${conversationId}`, {
                method: 'DELETE'
            });

            if (res.ok) {
                if (this.activeConversationId === conversationId) {
                    this.startNewChat();
                }
                this.loadConversations();
            }
        } catch (err) {
            console.error("Failed to delete conversation:", err);
        }
    }

    escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.sidebarController = new SidebarController();
});
