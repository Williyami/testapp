// Basic Auth Utilities

function saveAuthData(token, user) {
    if (token) {
        localStorage.setItem('authToken', token);
    }
    if (user && typeof user === 'object') {
        localStorage.setItem('userData', JSON.stringify(user)); // Store user object (includes role)
    }
}

function getToken() {
    return localStorage.getItem('authToken');
}

function getUserData() {
    const userDataString = localStorage.getItem('userData');
    try {
        return JSON.parse(userDataString);
    } catch (e) {
        return null;
    }
}

function getUserRole() {
    const userData = getUserData();
    return userData ? userData.role : null;
}

function clearAuthData() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
}

function redirectToLoginIfNoToken() {
    if (!getToken()) {
        // Ensure we are not already on login.html to avoid redirect loop
        if (!window.location.pathname.endsWith('login.html')) {
            window.location.href = 'login.html';
        }
    }
}
