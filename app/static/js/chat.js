/**
 * AuraAI Chat Workspace Controller - Stage 5 Markdown, Code Copy, Regenerate & Edit
 */

class ChatController {
    constructor() {
        this.messagesViewportEl = document.getElementById('messages-viewport');
        this.chatInputEl = document.getElementById('chat-input');
        this.sendBtnEl = document.getElementById('send-btn');
        this.stopBtnEl = document.getElementById('stop-btn');
        this.modelSelectEl = document.getElementById('model-select');
        this.welcomeScreenEl = document.getElementById('welcome-screen');
        this.activeConversationId = null;
        this.activeAbortController = null;

        this.configureMarked();
        this.init();
    }

    configureMarked() {
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                gfm: true,
                breaks: true
            });
        }
    }

    init() {
        if (this.chatInputEl) {
            // Auto-resize textarea
            this.chatInputEl.addEventListener('input', () => {
                this.chatInputEl.style.height = 'auto';
                this.chatInputEl.style.height = `${Math.min(this.chatInputEl.scrollHeight, 200)}px`;
            });

            // Enter key to send (Shift+Enter for newline)
            this.chatInputEl.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage();
                }
            });
        }

        if (this.sendBtnEl) {
            this.sendBtnEl.addEventListener('click', () => this.handleSendMessage());
        }

        if (this.stopBtnEl) {
            this.stopBtnEl.addEventListener('click', () => this.stopGeneration());
        }

        // Prompt Suggestion Cards
        document.querySelectorAll('.prompt-card').forEach(card => {
            card.addEventListener('click', () => {
                const promptText = card.dataset.prompt || card.querySelector('.prompt-card-title').textContent;
                if (this.chatInputEl) {
                    this.chatInputEl.value = promptText;
                    this.handleSendMessage();
                }
            });
        });
    }

    resetToWelcomeScreen() {
        this.activeConversationId = null;
        if (this.messagesViewportEl) {
            this.messagesViewportEl.innerHTML = '';
        }
        if (this.welcomeScreenEl) {
            this.welcomeScreenEl.style.display = 'flex';
        }
    }

    async loadConversationMessages(conversationId) {
        this.activeConversationId = conversationId;
        if (this.welcomeScreenEl) {
            this.welcomeScreenEl.style.display = 'none';
        }

        try {
            const response = await fetch(`/api/conversations/${conversationId}/messages`);
            if (!response.ok) return;

            const messages = await response.json();
            this.renderMessagesList(messages);
        } catch (err) {
            console.error("Failed to load messages:", err);
        }
    }

    renderMessagesList(messages) {
        if (!this.messagesViewportEl) return;
        this.messagesViewportEl.innerHTML = '';

        messages.forEach(msg => {
            this.appendMessageBubble(msg.role, msg.content, msg.id);
        });

        this.scrollToBottom();
    }

    appendMessageBubble(role, rawContent = '', messageId = null) {
        if (this.welcomeScreenEl) {
            this.welcomeScreenEl.style.display = 'none';
        }

        const isUser = role === 'user';
        const rowEl = document.createElement('div');
        rowEl.className = `message-row ${isUser ? 'user-row' : 'assistant-row'}`;
        if (messageId) rowEl.dataset.id = messageId;

        const avatarEl = document.createElement('div');
        avatarEl.className = `message-avatar ${isUser ? 'user-avatar-icon' : 'assistant-avatar-icon'}`;
        avatarEl.textContent = isUser ? 'U' : '✦';

        const bubbleEl = document.createElement('div');
        bubbleEl.className = 'message-bubble';

        if (!isUser) {
            const senderHeader = document.createElement('div');
            senderHeader.className = 'message-sender';
            senderHeader.innerHTML = `<span>AuraAI</span>`;
            bubbleEl.appendChild(senderHeader);
        }

        const contentEl = document.createElement('div');
        contentEl.className = 'markdown-body';
        this.renderFormattedContent(contentEl, rawContent);
        bubbleEl.appendChild(contentEl);

        // Actions toolbar
        const actionsEl = document.createElement('div');
        actionsEl.className = 'message-actions';

        if (isUser) {
            actionsEl.innerHTML = `
                <button class="msg-action-btn btn-edit" title="Edit message">✎ Edit</button>
                <button class="msg-action-btn btn-delete" title="Delete message">✕ Delete</button>
            `;
            actionsEl.querySelector('.btn-edit').addEventListener('click', () => this.handleEditUserMessage(rowEl, messageId, rawContent));
            actionsEl.querySelector('.btn-delete').addEventListener('click', () => this.handleDeleteMessage(rowEl, messageId));
        } else {
            actionsEl.innerHTML = `
                <button class="msg-action-btn btn-copy" title="Copy text">📋 Copy</button>
                <button class="msg-action-btn btn-regenerate" title="Regenerate response">↻ Regenerate</button>
                <button class="msg-action-btn btn-delete" title="Delete message">✕ Delete</button>
            `;
            actionsEl.querySelector('.btn-copy').addEventListener('click', (e) => this.copyToClipboard(contentEl.innerText, e.target));
            actionsEl.querySelector('.btn-regenerate').addEventListener('click', () => this.handleRegenerateResponse());
            actionsEl.querySelector('.btn-delete').addEventListener('click', () => this.handleDeleteMessage(rowEl, messageId));
        }

        bubbleEl.appendChild(actionsEl);

        if (!isUser) {
            rowEl.appendChild(avatarEl);
            rowEl.appendChild(bubbleEl);
        } else {
            rowEl.appendChild(bubbleEl);
            rowEl.appendChild(avatarEl);
        }

        this.messagesViewportEl.appendChild(rowEl);
        this.scrollToBottom();
        return { rowEl, bubbleEl, contentEl };
    }

    renderFormattedContent(containerEl, text) {
        if (!text) {
            containerEl.innerHTML = '';
            return;
        }

        if (typeof marked !== 'undefined') {
            const html = marked.parse(text);
            containerEl.innerHTML = html;
            this.enhanceCodeBlocks(containerEl);
        } else {
            containerEl.textContent = text;
        }
    }

    enhanceCodeBlocks(containerEl) {
        containerEl.querySelectorAll('pre code').forEach((codeBlock) => {
            const preEl = codeBlock.parentElement;
            if (preEl.parentElement.classList.contains('code-block-container')) return;

            // Apply syntax highlighting
            if (typeof hljs !== 'undefined') {
                hljs.highlightElement(codeBlock);
            }

            // Extract language label
            let lang = 'code';
            codeBlock.classList.forEach(cls => {
                if (cls.startsWith('language-')) {
                    lang = cls.replace('language-', '');
                }
            });

            // Wrap in styled block container
            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-container';

            const header = document.createElement('div');
            header.className = 'code-block-header';
            header.innerHTML = `
                <span>${lang.toUpperCase()}</span>
                <button class="code-block-copy-btn">📋 Copy code</button>
            `;

            header.querySelector('.code-block-copy-btn').addEventListener('click', (e) => {
                this.copyToClipboard(codeBlock.innerText, e.target);
            });

            preEl.parentNode.insertBefore(wrapper, preEl);
            wrapper.appendChild(header);
            wrapper.appendChild(preEl);
        });
    }

    copyToClipboard(text, buttonEl) {
        navigator.clipboard.writeText(text).then(() => {
            const originalText = buttonEl.textContent;
            buttonEl.textContent = '✓ Copied!';
            setTimeout(() => {
                buttonEl.textContent = originalText;
            }, 2000);
        }).catch(err => console.error("Clipboard write failed:", err));
    }

    stopGeneration() {
        if (this.activeAbortController) {
            this.activeAbortController.abort();
            this.activeAbortController = null;
        }
        if (this.stopBtnEl) this.stopBtnEl.style.display = 'none';
    }

    async handleSendMessage() {
        const text = this.chatInputEl ? this.chatInputEl.value.trim() : '';
        if (!text) return;

        this.chatInputEl.value = '';
        this.chatInputEl.style.height = 'auto';

        this.appendMessageBubble('user', text);
        const assistantBubble = this.appendMessageBubble('assistant', '');
        assistantBubble.contentEl.innerHTML = '<span style="opacity:0.5; font-style:italic;">AuraAI is thinking...</span>';

        this.activeAbortController = new AbortController();
        if (this.stopBtnEl) this.stopBtnEl.style.display = 'inline-flex';

        try {
            const selectedModel = this.modelSelectEl ? this.modelSelectEl.value : null;
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_id: this.activeConversationId,
                    content: text,
                    model: selectedModel
                }),
                signal: this.activeAbortController.signal
            });

            if (!response.ok) throw new Error("Failed to send message to server");

            await this.consumeSSEResponse(response, assistantBubble);
        } catch (err) {
            if (err.name === 'AbortError') {
                assistantBubble.contentEl.innerHTML += ' <em>[Generation stopped]</em>';
            } else {
                assistantBubble.contentEl.textContent = `Error: ${err.message}`;
            }
        } finally {
            this.stopGeneration();
        }
    }

    async handleRegenerateResponse() {
        if (!this.activeConversationId) return;

        const assistantBubble = this.appendMessageBubble('assistant', '');
        assistantBubble.contentEl.innerHTML = '<span style="opacity:0.5; font-style:italic;">Regenerating response...</span>';

        this.activeAbortController = new AbortController();
        if (this.stopBtnEl) this.stopBtnEl.style.display = 'inline-flex';

        try {
            const selectedModel = this.modelSelectEl ? this.modelSelectEl.value : null;
            const response = await fetch('/api/chat/regenerate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_id: this.activeConversationId,
                    model: selectedModel
                }),
                signal: this.activeAbortController.signal
            });

            if (!response.ok) throw new Error("Failed to regenerate response");

            await this.consumeSSEResponse(response, assistantBubble);
        } catch (err) {
            if (err.name !== 'AbortError') {
                assistantBubble.contentEl.textContent = `Error: ${err.message}`;
            }
        } finally {
            this.stopGeneration();
        }
    }

    async handleEditUserMessage(rowEl, messageId, currentContent) {
        if (!messageId) return;

        const bubbleEl = rowEl.querySelector('.message-bubble');
        bubbleEl.innerHTML = `
            <div class="inline-edit-box">
                <textarea class="inline-edit-textarea">${this.escapeHtml(currentContent)}</textarea>
                <div class="flex gap-2 justify-between">
                    <button class="btn btn-secondary btn-cancel-edit" style="padding:0.25rem 0.5rem; font-size:var(--font-size-xs);">Cancel</button>
                    <button class="btn btn-primary btn-save-edit" style="padding:0.25rem 0.5rem; font-size:var(--font-size-xs);">Save & Submit</button>
                </div>
            </div>
        `;

        bubbleEl.querySelector('.btn-cancel-edit').addEventListener('click', () => {
            this.loadConversationMessages(this.activeConversationId);
        });

        bubbleEl.querySelector('.btn-save-edit').addEventListener('click', async () => {
            const newText = bubbleEl.querySelector('.inline-edit-textarea').value.trim();
            if (!newText || newText === currentContent) {
                this.loadConversationMessages(this.activeConversationId);
                return;
            }

            // Remove trailing rows in viewport
            let current = rowEl.nextElementSibling;
            while (current) {
                const next = current.nextElementSibling;
                current.remove();
                current = next;
            }

            // Render fresh assistant placeholder
            const assistantBubble = this.appendMessageBubble('assistant', '');
            assistantBubble.contentEl.innerHTML = '<span style="opacity:0.5; font-style:italic;">AuraAI is thinking...</span>';

            this.activeAbortController = new AbortController();
            if (this.stopBtnEl) this.stopBtnEl.style.display = 'inline-flex';

            try {
                const response = await fetch('/api/chat/edit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message_id: messageId,
                        new_content: newText
                    }),
                    signal: this.activeAbortController.signal
                });

                if (!response.ok) throw new Error("Failed to edit message");

                await this.consumeSSEResponse(response, assistantBubble);
            } catch (err) {
                if (err.name !== 'AbortError') {
                    assistantBubble.contentEl.textContent = `Error: ${err.message}`;
                }
            } finally {
                this.stopGeneration();
            }
        });
    }

    async handleDeleteMessage(rowEl, messageId) {
        if (!messageId) return;
        try {
            const res = await fetch(`/api/chat/messages/${messageId}`, { method: 'DELETE' });
            if (res.ok) {
                rowEl.remove();
            }
        } catch (err) {
            console.error("Failed to delete message:", err);
        }
    }

    async consumeSSEResponse(response, assistantBubble) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let accumulatedText = "";
        let isFirstChunk = true;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split("\n\n");

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    try {
                        const jsonStr = line.replace("data: ", "").trim();
                        if (!jsonStr) continue;
                        const payload = JSON.parse(jsonStr);

                        if (payload.type === 'meta') {
                            if (payload.conversation_id && !this.activeConversationId) {
                                this.activeConversationId = payload.conversation_id;
                            }
                        } else if (payload.type === 'chunk') {
                            if (isFirstChunk) {
                                assistantBubble.contentEl.textContent = "";
                                isFirstChunk = false;
                            }
                            accumulatedText += payload.content;
                            this.renderFormattedContent(assistantBubble.contentEl, accumulatedText);
                            this.scrollToBottom();
                        } else if (payload.type === 'done') {
                            if (window.sidebarController) {
                                window.sidebarController.activeConversationId = this.activeConversationId;
                                window.sidebarController.loadConversations();
                            }
                        } else if (payload.type === 'error') {
                            assistantBubble.contentEl.textContent += `\n[Error: ${payload.message}]`;
                        }
                    } catch (e) {
                        // Non-critical SSE fragment
                    }
                }
            }
        }
    }

    scrollToBottom() {
        if (this.messagesViewportEl) {
            this.messagesViewportEl.scrollTop = this.messagesViewportEl.scrollHeight;
        }
    }

    escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.chatController = new ChatController();
});
