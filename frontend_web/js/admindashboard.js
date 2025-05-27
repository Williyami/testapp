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

    fetchAndDisplayAdminExpenses(); // Fetch and display expenses
});

async function fetchAndDisplayAdminExpenses() {
    const token = getToken(); // From auth_utils.js
    if (!token) {
        // This case should ideally be caught by redirectToLoginIfNoToken,
        // but as a fallback:
        displayErrorMessage('Authentication token not found. Please log in again.');
        return;
    }

    const expensesTableBody = document.getElementById('expensesTableBody');
    const expensesMessage = document.getElementById('expensesMessage');

    if (!expensesTableBody || !expensesMessage) {
        console.error('Required table elements (expensesTableBody or expensesMessage) not found in the DOM.');
        return;
    }

    // Clear previous content and show loading message
    expensesTableBody.innerHTML = '';
    expensesMessage.textContent = 'Loading expenses...';
    expensesMessage.className = 'text-blue-600 text-base mb-4'; // Style for loading message

    try {
        const response = await fetch('/api/admin/expenses', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const expenses = await response.json();
            if (expenses && expenses.length > 0) {
                expensesMessage.textContent = ''; // Clear loading message
                expenses.forEach(expense => {
                    const row = expensesTableBody.insertRow();
                    row.insertCell().textContent = expense.employee_id || 'N/A';
                    row.insertCell().textContent = expense.amount ? expense.amount.toFixed(2) : '0.00';
                    row.insertCell().textContent = expense.currency || 'N/A';
                    row.insertCell().textContent = expense.date ? new Date(expense.date).toLocaleDateString() : 'N/A';
                    row.insertCell().textContent = expense.vendor || 'N/A';
                    row.insertCell().textContent = expense.description || 'N/A';
                    
                    // Style status based on its value
                    const statusCell = row.insertCell();
                    statusCell.textContent = expense.status || 'N/A';
                    if (expense.status === 'approved') {
                        statusCell.className = 'text-green-600 font-semibold';
                    } else if (expense.status === 'rejected') {
                        statusCell.className = 'text-red-600 font-semibold';
                    } else if (expense.status === 'pending') {
                        statusCell.className = 'text-yellow-600 font-semibold';
                    }
                    
                    const actionsCell = row.insertCell();
                    if (expense.status === 'pending') {
                        const approveButton = document.createElement('button');
                        approveButton.textContent = 'Approve';
                        approveButton.className = 'bg-green-500 hover:bg-green-700 text-white text-xs py-1 px-2 rounded mr-1';
                        approveButton.setAttribute('data-expense-id', expense.id);
                        approveButton.setAttribute('data-action', 'approve');
                        actionsCell.appendChild(approveButton);

                        const rejectButton = document.createElement('button');
                        rejectButton.textContent = 'Reject';
                        rejectButton.className = 'bg-red-500 hover:bg-red-700 text-white text-xs py-1 px-2 rounded';
                        rejectButton.setAttribute('data-expense-id', expense.id);
                        rejectButton.setAttribute('data-action', 'reject');
                        actionsCell.appendChild(rejectButton);
                    } else {
                        actionsCell.textContent = 'N/A'; // Or leave empty
                    }
                });
            } else {
                expensesMessage.textContent = 'No expenses submitted yet.';
                expensesMessage.className = 'text-gray-500 text-base mb-4';
            }
        } else {
            const errorData = await response.json().catch(() => ({ error: 'Failed to retrieve error details.' }));
            let errorMessage = `Error fetching expenses: ${response.status} ${response.statusText}`;
            if (errorData && errorData.error) {
                errorMessage += ` - ${errorData.error}`;
            }
            if (response.status === 401 || response.status === 403) {
                errorMessage = 'Unauthorized or session expired. Please log in again.';
                // Optional: redirect to login after a short delay or display a login button
                clearAuthData();
                window.location.href = 'login.html';
            }
            displayErrorMessage(errorMessage);
        }
    } catch (error) {
        console.error('Network or other error fetching expenses:', error);
        displayErrorMessage('Failed to fetch expenses due to a network or server error. Please try again later.');
    }
}

function displayErrorMessage(message) {
    const expensesMessage = document.getElementById('expensesMessage');
    if (expensesMessage) {
        expensesMessage.textContent = message;
        expensesMessage.className = 'text-red-600 text-base mb-4 font-semibold'; // Style for error messages
    }
}

// Event delegation for approve/reject buttons
document.addEventListener('DOMContentLoaded', function () {
    // ... (existing DOMContentLoaded code) ...

    const expensesTableBody = document.getElementById('expensesTableBody');
    if (expensesTableBody) {
        expensesTableBody.addEventListener('click', async function (event) {
            const target = event.target;
            const action = target.getAttribute('data-action');
            const expenseId = target.getAttribute('data-expense-id');

            if (!action || !expenseId) {
                return; // Clicked on something else
            }

            if (action === 'approve') {
                await handleExpenseAction(expenseId, 'approve', target);
            } else if (action === 'reject') {
                await handleExpenseAction(expenseId, 'reject', target);
            }
        });
    }
});

async function handleExpenseAction(expenseId, actionType, buttonElement) {
    const token = getToken();
    if (!token) {
        displayErrorMessage('Authentication token not found. Please log in.');
        redirectToLoginIfNoToken(); // Ensure redirection
        return;
    }

    const endpoint = `/api/admin/expenses/${expenseId}/${actionType}`;
    const successMessage = `Expense ${actionType}d successfully.`;
    const newStatus = actionType === 'approve' ? 'approved' : 'rejected';

    // Disable button to prevent multiple clicks
    buttonElement.disabled = true;
    const otherButtonAction = actionType === 'approve' ? 'reject' : 'approve';
    const otherButton = buttonElement.parentElement.querySelector(`button[data-action="${otherButtonAction}"]`);
    if(otherButton) otherButton.disabled = true;


    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json' // Though body is empty, good practice
            }
        });

        if (response.ok) {
            // Update UI
            const row = buttonElement.closest('tr');
            if (row) {
                // Assuming status is the 7th cell (index 6)
                const statusCell = row.cells[6]; 
                statusCell.textContent = newStatus;
                statusCell.className = newStatus === 'approved' ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold';
                
                // Remove buttons from actions cell (8th cell, index 7)
                const actionsCell = row.cells[7];
                actionsCell.innerHTML = newStatus === 'approved' ? 'Approved' : 'Rejected'; // Or just 'N/A'
            }
            // Display temporary success message (optional)
            const expensesMessage = document.getElementById('expensesMessage');
            if (expensesMessage) {
                expensesMessage.textContent = successMessage;
                expensesMessage.className = 'text-green-600 text-base mb-4 font-semibold';
                setTimeout(() => { if(expensesMessage.textContent === successMessage) expensesMessage.textContent = ''; }, 3000);
            }
        } else {
            const errorData = await response.json().catch(() => ({ error: `Failed to ${actionType} expense.` }));
            let errorMessage = `Error ${actionType}ing expense: ${response.status} ${response.statusText}`;
            if (errorData && errorData.error) {
                errorMessage += ` - ${errorData.error}`;
            }
            if (response.status === 401 || response.status === 403) {
                errorMessage = 'Unauthorized or session expired. Please log in again.';
                clearAuthData();
                window.location.href = 'login.html';
            }
            displayErrorMessage(errorMessage);
            // Re-enable buttons on failure if not an auth error
            if (response.status !== 401 && response.status !== 403) {
                buttonElement.disabled = false;
                if(otherButton) otherButton.disabled = false;
            }
        }
    } catch (error) {
        console.error(`Network or other error during ${actionType} action:`, error);
        displayErrorMessage(`Failed to ${actionType} expense due to a network or server error.`);
        buttonElement.disabled = false; // Re-enable button
        if(otherButton) otherButton.disabled = false;
    }
}
