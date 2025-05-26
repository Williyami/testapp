document.addEventListener('DOMContentLoaded', function () {
    const API_BASE_URL = 'http://127.0.0.1:5000'; // Added this line
    redirectToLoginIfNoToken(); // From auth_utils.js

    const expenseForm = document.getElementById('expenseForm');
    const submitButton = document.getElementById('submitExpenseButton');
    const messageContainer = document.getElementById('message-container');

    const expenseNameInput = document.getElementById('expenseName');
    const categorySelect = document.getElementById('expenseCategory');
    const amountInput = document.getElementById('expenseAmount');
    const dateInput = document.getElementById('expenseDate');
    const notesTextarea = document.getElementById('expenseNotes');
    const receiptInput = document.getElementById('receiptFile');
    const topPlusButton = document.getElementById('addExpenseTopButton');
    const logoutButton = document.getElementById('logoutButtonExpensesPage'); 

    if (logoutButton) {
        logoutButton.addEventListener('click', function () {
            clearAuthData(); // From auth_utils.js
            window.location.href = 'login.html';
        });
    } else {
        console.warn('Logout button (id="logoutButtonExpensesPage") not found on expenses.html.');
    }

    if (!expenseForm || !submitButton || !messageContainer || !receiptInput || !expenseNameInput || !categorySelect || !amountInput || !dateInput || !notesTextarea) {
        console.error('Essential page elements not found. Check IDs for form, submit button, message container, receipt input, and all form fields.');
        if (messageContainer) {
            messageContainer.textContent = 'Error: Page initialization failed. Required elements are missing.';
            messageContainer.style.color = 'red';
        }
        return;
    }

    const displayMessage = (message, type = 'error') => {
        if (!messageContainer) return;
        messageContainer.textContent = message;
        messageContainer.style.color = type === 'success' ? 'green' : 'red';
        messageContainer.style.border = `1px solid ${type === 'success' ? 'green' : 'red'}`;
        messageContainer.style.borderRadius = '5px';
        messageContainer.style.padding = '10px';
        messageContainer.style.marginTop = '10px';
        messageContainer.style.marginBottom = '10px';
    };

    submitButton.addEventListener('click', async function (event) {
        event.preventDefault();
        displayMessage(''); 

        const formData = new FormData();
        formData.append('vendor', expenseNameInput.value);
        formData.append('category', categorySelect.value);
        formData.append('amount', amountInput.value);
        formData.append('date', dateInput.value);
        formData.append('description', notesTextarea.value);

        if (receiptInput.files && receiptInput.files[0]) {
            formData.append('receipt', receiptInput.files[0]);
        } else {
            displayMessage('Receipt file is required.', 'error');
            return;
        }
        
        if (!expenseNameInput.value || !amountInput.value || !dateInput.value) {
            displayMessage('Please fill in Expense Name, Amount, and Date.', 'error');
            return;
        }
        if (dateInput.value && !/^\d{4}-\d{2}-\d{2}$/.test(dateInput.value)) {
            displayMessage('Please enter the date in YYYY-MM-DD format.', 'error');
            return;
        }

        try {
            const authToken = getToken(); // Use getToken() from auth_utils.js
            if (!authToken) {
                displayMessage('Authentication token not found. Please log in.', 'error');
                return;
            }

            // Note: The fetch URL will be updated in a subsequent subtask to use API_BASE_URL
            const response = await fetch(API_BASE_URL + '/expenses', { // Updated to use API_BASE_URL
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + authToken
                },
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                displayMessage('Expense submitted successfully! ID: ' + result.expense.id, 'success');
                if(expenseForm) expenseForm.reset();
            } else {
                 if (response.status === 401) { // Unauthorized or token expired
                    clearAuthData();
                    redirectToLoginIfNoToken();
                }
                displayMessage('Error submitting expense: ' + (result.error || response.statusText || 'Unknown server error'), 'error');
            }
        } catch (error) {
            console.error('Submission error:', error);
            displayMessage('Network error or server is down. ' + error.message, 'error');
        }
    });

    if (topPlusButton && expenseForm) {
        topPlusButton.addEventListener('click', () => {
            console.log('Top Plus button clicked - clearing form.');
            if(expenseForm) expenseForm.reset();
            displayMessage(''); 
        });
    }
});
