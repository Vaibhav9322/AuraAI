/**
 * AuraAI User Settings Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    const themeDarkBtn = document.getElementById('theme-dark-btn');
    const themeLightBtn = document.getElementById('theme-light-btn');
    const defaultModelSelect = document.getElementById('settings-default-model');
    const responseStyleSelect = document.getElementById('settings-response-style');
    const customPromptInput = document.getElementById('settings-custom-prompt');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const settingsAlert = document.getElementById('settings-alert');

    let currentTheme = 'dark';

    // Load initial settings
    fetch('/api/settings')
        .then(res => res.json())
        .then(data => {
            if (data.theme) {
                setTheme(data.theme);
            }
            if (defaultModelSelect && data.default_model) {
                defaultModelSelect.value = data.default_model;
            }
            if (responseStyleSelect && data.response_style) {
                responseStyleSelect.value = data.response_style;
            }
            if (customPromptInput && data.custom_system_prompt) {
                customPromptInput.value = data.custom_system_prompt;
            }
        })
        .catch(err => console.error("Failed to load settings:", err));

    function setTheme(theme) {
        currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);

        if (themeDarkBtn && themeLightBtn) {
            if (theme === 'dark') {
                themeDarkBtn.classList.add('active');
                themeLightBtn.classList.remove('active');
            } else {
                themeLightBtn.classList.add('active');
                themeDarkBtn.classList.remove('active');
            }
        }
    }

    if (themeDarkBtn) {
        themeDarkBtn.addEventListener('click', () => setTheme('dark'));
    }
    if (themeLightBtn) {
        themeLightBtn.addEventListener('click', () => setTheme('light'));
    }

    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', async () => {
            try {
                saveSettingsBtn.disabled = true;
                saveSettingsBtn.textContent = 'Saving...';

                const payload = {
                    theme: currentTheme,
                    default_model: defaultModelSelect ? defaultModelSelect.value : 'llama-3.3-70b-versatile',
                    response_style: responseStyleSelect ? responseStyleSelect.value : 'balanced',
                    custom_system_prompt: customPromptInput ? customPromptInput.value.trim() : ''
                };

                const res = await fetch('/api/settings', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    if (settingsAlert) {
                        settingsAlert.textContent = '✓ Settings saved successfully!';
                        settingsAlert.className = 'auth-alert auth-alert-success';
                        settingsAlert.style.display = 'flex';
                        setTimeout(() => { settingsAlert.style.display = 'none'; }, 3000);
                    }
                }
            } catch (err) {
                console.error("Save settings error:", err);
            } finally {
                saveSettingsBtn.disabled = false;
                saveSettingsBtn.textContent = 'Save Settings';
            }
        });
    }
});
