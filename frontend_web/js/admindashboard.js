document.addEventListener('DOMContentLoaded', function () {
    // Initial auth checks
    redirectToLoginIfNoToken(); // From auth_utils.js

    const userRole = getUserRole(); // From auth_utils.js
    if (userRole !== 'admin') {
        // If not admin, redirect to login (or employee dashboard if appropriate)
        alert('Access denied. You must be an admin to view this page.'); // Optional alert
        clearAuthData(); // Clear any partial/incorrect auth data
        window.location.href = 'login.html';
        return; // Stop further script execution
    }

    // Logout button functionality
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', function () {
            clearAuthData(); // From auth_utils.js
            window.location.href = 'login.html';
        });
    } else {
        console.warn('Logout button (id="logoutButton") not found on admindashboard.html.');
    }

    // Other admin dashboard specific JavaScript can go here...
    console.log('Admin dashboard loaded for admin user.');
});
