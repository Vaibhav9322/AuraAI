/**
 * AuraAI Authentication Client JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const alertBox = document.getElementById('auth-alert');

    function showAlert(message, type = 'error') {
        if (!alertBox) return;
        alertBox.textContent = message;
        alertBox.className = `auth-alert auth-alert-${type}`;
        alertBox.style.display = 'flex';
    }

    function hideAlert() {
        if (!alertBox) return;
        alertBox.style.display = 'none';
    }

    function parseErrorMessage(data, fallbackMessage) {
        if (data && data.detail) {
            if (typeof data.detail === 'string') {
                return data.detail;
            }
            if (Array.isArray(data.detail)) {
                return data.detail.map(item => item.msg || item.message || JSON.stringify(item)).join(' | ');
            }
        }
        return fallbackMessage;
    }

    // Login Form Handler
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();

            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;

            const identifier = document.getElementById('email_or_username').value.trim();
            const password = document.getElementById('password').value;

            if (!identifier || !password) {
                showAlert('Please fill in all fields.');
                return;
            }

            try {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Signing in...';

                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email_or_username: identifier,
                        password: password
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(parseErrorMessage(data, 'Failed to sign in. Check your credentials.'));
                }

                // Successful login -> Redirect to main chat interface
                showAlert('Signed in successfully! Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = '/chat';
                }, 600);

            } catch (err) {
                showAlert(err.message);
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }

    // Register Form Handler
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();

            const submitBtn = registerForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;

            const email = document.getElementById('email').value.trim();
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;

            if (!email || !username || !password || !confirmPassword) {
                showAlert('Please fill in all fields.');
                return;
            }

            if (password !== confirmPassword) {
                showAlert('Passwords do not match.');
                return;
            }

            if (password.length < 6) {
                showAlert('Password must be at least 6 characters long.');
                return;
            }

            try {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Creating Account...';

                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: email,
                        username: username,
                        password: password
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(parseErrorMessage(data, 'Failed to register account.'));
                }

                // Successful registration -> Redirect to main chat interface
                showAlert('Account created! Redirecting to workspace...', 'success');
                setTimeout(() => {
                    window.location.href = '/chat';
                }, 600);

            } catch (err) {
                showAlert(err.message);
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }
});
