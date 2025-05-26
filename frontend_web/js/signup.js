document.addEventListener('DOMContentLoaded', function () {
    const API_BASE_URL = 'http://127.0.0.1:5000'; // Added this line

    const signupForm = document.getElementById('signupForm');
    const signupButton = document.getElementById('signupButton');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const messageContainer = document.getElementById('message-container');

    if (!signupForm || !signupButton || !usernameInput || !passwordInput || !confirmPasswordInput || !messageContainer) {
        console.error('Signup form elements not found!');
        if (messageContainer) messageContainer.textContent = 'Page error. Please refresh.';
        return;
    }

    // Helper to display messages (similar to login.js)
    const displayMessage = (message, type = 'error') => {
        messageContainer.textContent = message;
        messageContainer.className = 'message'; // Reset classes
        if (type === 'success') {
            messageContainer.classList.add('success');
        } else {
            messageContainer.classList.add('error');
        }
    };

    signupForm.addEventListener('submit', async function (event) {
        event.preventDefault();
        displayMessage(''); // Clear previous messages

        const username = usernameInput.value.trim();
        const password = passwordInput.value; // Don't trim password, spaces can be intentional
        const confirmPassword = confirmPasswordInput.value;

        // Client-side validation
        if (!username || !password || !confirmPassword) {
            displayMessage('All fields are required.', 'error');
            return;
        }
        if (password !== confirmPassword) {
            displayMessage('Passwords do not match.', 'error');
            return;
        }
        if (password.length < 8) {
            displayMessage('Password must be at least 8 characters long.', 'error');
            return;
        }

        try {
            // Note: The fetch URL will be updated in a subsequent subtask to use API_BASE_URL
            const response = await fetch(API_BASE_URL + '/signup', { // Updated to use API_BASE_URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password }) 
                // Role defaults to 'employee' on the backend for this public endpoint
            });

            const result = await response.json();

            if (response.ok) {
                displayMessage(result.message || 'Account created successfully! Redirecting to login...', 'success');
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 2000); // Wait 2 seconds before redirecting
            } else {
                displayMessage(result.error || 'Signup failed. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Signup error:', error);
            displayMessage('An error occurred during signup. Please try again.', 'error');
        }
    });
});
