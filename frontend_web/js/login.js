document.addEventListener('DOMContentLoaded', function () {
    const API_BASE_URL = 'http://127.0.0.1:5000'; // Added this line

    const loginForm = document.getElementById('loginForm');
    const loginButton = document.getElementById('loginButton');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const messageContainer = document.getElementById('message-container');

    if (!loginForm || !loginButton || !usernameInput || !passwordInput || !messageContainer) {
        console.error('Login form elements not found!');
        return;
    }
    
    // Check if already logged in and redirect appropriately
    const existingToken = getToken(); // Assumes getToken is from auth_utils.js, which should be loaded
    const existingUserRole = getUserRole(); // Assumes getUserRole is from auth_utils.js
    if (existingToken && existingUserRole) {
        if (existingUserRole === 'admin') {
            window.location.href = 'admindashboard.html';
        } else if (existingUserRole === 'employee') {
            window.location.href = 'expense_overview.html';
        }
        return; // Stop further execution if redirected
    }


    const displayMessage = (message, type = 'error') => {
        messageContainer.textContent = message;
        messageContainer.className = 'message'; // Reset classes
        if (type === 'success') {
            messageContainer.classList.add('success');
        } else {
            messageContainer.classList.add('error');
        }
    };

    loginForm.addEventListener('submit', async function (event) {
        event.preventDefault();
        displayMessage(''); // Clear previous messages

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        if (!username || !password) {
            displayMessage('Username and password are required.', 'error');
            return;
        }

        try {
            // Note: The fetch URL will be updated in a subsequent subtask to use API_BASE_URL
            const response = await fetch(API_BASE_URL + '/login', { // Updated to use API_BASE_URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const result = await response.json();

            if (response.ok && result.token && result.user) {
                saveAuthData(result.token, result.user); // Save token and user data (which includes role)
                
                displayMessage('Login successful! Redirecting...', 'success');

                // Redirect based on role
                if (result.user.role === 'admin') {
                    window.location.href = 'admindashboard.html';
                } else if (result.user.role === 'employee') {
                    window.location.href = 'expense_overview.html';
                } else {
                    displayMessage('Login successful, but role unknown. Cannot redirect.', 'error');
                }
            } else {
                displayMessage(result.error || 'Login failed. Please check your credentials.', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            displayMessage('An error occurred during login. Please try again.', 'error');
        }
    });
});
