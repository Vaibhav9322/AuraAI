/**
 * AuraAI Files & Document Attachment Controller
 */

class FilesController {
    constructor() {
        this.fileInputEl = document.getElementById('file-upload-input');
        this.attachBtnEl = document.getElementById('attach-file-btn');
        this.previewContainerEl = document.getElementById('attachment-preview-container');
        this.pendingAttachments = []; // Array of attachment objects { id, filename, file_size }

        this.init();
    }

    init() {
        if (this.attachBtnEl && this.fileInputEl) {
            this.attachBtnEl.addEventListener('click', () => this.fileInputEl.click());
            this.fileInputEl.addEventListener('change', (e) => this.handleFileSelect(e));
        }
    }

    async handleFileSelect(event) {
        const files = event.target.files;
        if (!files || files.length === 0) return;

        for (const file of files) {
            await this.uploadSingleFile(file);
        }

        // Reset input value
        this.fileInputEl.value = '';
    }

    async uploadSingleFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        if (window.chatController && window.chatController.activeConversationId) {
            formData.append('conversation_id', window.chatController.activeConversationId);
        }

        try {
            this.showUploadingState(file.name);

            const response = await fetch('/api/files/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to upload file.');
            }

            // Successfully uploaded
            this.pendingAttachments.push(data);
            this.renderAttachmentPill(data);

            if (data.conversation_id && window.chatController) {
                window.chatController.activeConversationId = data.conversation_id;
            }

        } catch (err) {
            alert(`File Upload Error: ${err.message}`);
        } finally {
            this.removeUploadingState();
        }
    }

    renderAttachmentPill(attachment) {
        if (!this.previewContainerEl) return;
        this.previewContainerEl.style.display = 'flex';

        const pill = document.createElement('div');
        pill.className = 'attachment-pill';
        pill.dataset.id = attachment.id;

        const sizeKb = Math.round(attachment.file_size / 1024);

        pill.innerHTML = `
            <span>📄 ${this.escapeHtml(attachment.filename)} (${sizeKb} KB)</span>
            <button class="remove-pill-btn" title="Remove attachment">✕</button>
        `;

        pill.querySelector('.remove-pill-btn').addEventListener('click', () => {
            this.deleteAttachment(attachment.id, pill);
        });

        this.previewContainerEl.appendChild(pill);
    }

    async deleteAttachment(attachmentId, pillElement) {
        try {
            await fetch(`/api/files/${attachmentId}`, { method: 'DELETE' });
            this.pendingAttachments = this.pendingAttachments.filter(a => a.id !== attachmentId);
            pillElement.remove();

            if (this.pendingAttachments.length === 0 && this.previewContainerEl) {
                this.previewContainerEl.style.display = 'none';
            }
        } catch (err) {
            console.error("Failed to delete attachment:", err);
        }
    }

    showUploadingState(filename) {
        if (this.attachBtnEl) {
            this.attachBtnEl.disabled = true;
            this.attachBtnEl.style.opacity = '0.5';
        }
    }

    removeUploadingState() {
        if (this.attachBtnEl) {
            this.attachBtnEl.disabled = false;
            this.attachBtnEl.style.opacity = '1';
        }
    }

    clearPendingAttachments() {
        this.pendingAttachments = [];
        if (this.previewContainerEl) {
            this.previewContainerEl.innerHTML = '';
            this.previewContainerEl.style.display = 'none';
        }
    }

    escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.filesController = new FilesController();
});
