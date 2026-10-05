/**
 * AuraAI Client Application JS - Stage 1 Initialization
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("AuraAI Stage 1 Application Initialized.");

    const dbBadge = document.getElementById('db-status-badge');
    const aiProviderValue = document.getElementById('ai-provider-value');
    const aiModelValue = document.getElementById('ai-model-value');

    // Asynchronously fetch server health status
    fetch('/api/health')
        .then(res => res.json())
        .then(data => {
            console.log("Server Health:", data);
            if (dbBadge) {
                if (data.database_connected) {
                    dbBadge.className = 'badge badge-success';
                    dbBadge.textContent = 'Connected (MySQL)';
                } else {
                    dbBadge.className = 'badge badge-warning';
                    dbBadge.textContent = 'Disconnected';
                }
            }
            if (aiProviderValue && data.ai_provider) {
                aiProviderValue.textContent = data.ai_provider.toUpperCase();
            }
            if (aiModelValue && data.ai_model) {
                aiModelValue.textContent = data.ai_model;
            }
        })
        .catch(err => {
            console.error("Failed to connect to health API:", err);
            if (dbBadge) {
                dbBadge.className = 'badge badge-warning';
                dbBadge.textContent = 'API Error';
            }
        });
});
