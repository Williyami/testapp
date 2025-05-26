document.addEventListener('DOMContentLoaded', function () {
    const recentSubmissionsContainer = document.getElementById('recentSubmissionsContainer');
    const pastExpensesContainer = document.getElementById('pastExpensesContainer');
    const addExpenseButton = document.getElementById('addExpenseButton'); // Plus button
    const searchInput = document.getElementById('searchExpensesInput');
    const searchButton = document.getElementById('searchExpensesButton'); // The magnifying glass icon button part
    const categoryFilterButton = document.getElementById('categoryFilterButton');
    const dateFilterButton = document.getElementById('dateFilterButton');
    const statusFilterButton = document.getElementById('statusFilterButton');
    const chatWithAIButton = document.getElementById('chatWithAIButton');

    // Helper function to create an expense item element
    const createExpenseItemHTML = (expense) => {
        // Determine status color, default to something neutral if status is unknown
        let statusColor = 'bg-gray-400'; // Default for pending or unknown
        let statusText = expense.status || 'Pending'; // Display status text

        if (expense.status && expense.status.toLowerCase() === 'approved') {
            statusColor = 'bg-[#07883d]'; // Green for approved
        } else if (expense.status && expense.status.toLowerCase() === 'rejected') {
            statusColor = 'bg-red-500'; // Red for rejected
        }
        // Add more conditions for other statuses like 'pending', 'processing', etc.

        // For "Recent Submissions", show a dot. For "Past Expenses", show text.
        // This will require knowing which container we are rendering to, or having two different render functions.
        // For now, let's make it simple and use the dot for all.
        // The original HTML had text for "Past Expenses" status.
        // We'll use a generic structure and adapt if needed.

        return `
            <div class="flex items-center gap-4 bg-white px-4 min-h-[72px] py-2 justify-between expense-item">
                <div class="flex items-center gap-4">
                    <div class="text-[#121317] flex items-center justify-center rounded-lg bg-[#f1f1f4] shrink-0 size-12" data-icon="Receipt" data-size="24px" data-weight="regular">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256">
                            <path d="M72,104a8,8,0,0,1,8-8h96a8,8,0,0,1,0,16H80A8,8,0,0,1,72,104Zm8,40h96a8,8,0,0,0,0-16H80a8,8,0,0,0,0,16ZM232,56V208a8,8,0,0,1-11.58,7.15L192,200.94l-28.42,14.21a8,8,0,0,1-7.16,0L128,200.94,99.58,215.15a8,8,0,0,1-7.16,0L64,200.94,35.58,215.15A8,8,0,0,1,24,208V56A16,16,0,0,1,40,40H216A16,16,0,0,1,232,56Zm-16,0H40V195.06l20.42-10.22a8,8,0,0,1,7.16,0L96,199.06l28.42-14.22a8,8,0,0,1,7.16,0L160,199.06l28.42-14.22a8,8,0,0,1,7.16,0L216,195.06Z"></path>
                        </svg>
                    </div>
                    <div class="flex flex-col justify-center">
                        <p class="text-[#121317] text-base font-medium leading-normal line-clamp-1">${expense.vendor || 'N/A'}</p>
                        <p class="text-[#686e82] text-sm font-normal leading-normal line-clamp-2">
                            ${expense.currency ? expense.currency + ' ' : ''}${expense.amount ? expense.amount.toFixed(2) : '0.00'} - ${new Date(expense.date).toLocaleDateString()}
                        </p>
                    </div>
                </div>
                <div class="shrink-0">
                    <div class="flex size-7 items-center justify-center">
                        <div class="size-3 rounded-full ${statusColor}" title="${statusText}"></div>
                    </div>
                </div>
            </div>
        `;
    };

    // Function to fetch and render expenses
    const loadExpenses = async () => {
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            if(recentSubmissionsContainer) recentSubmissionsContainer.innerHTML = '<p class="px-4 text-red-500">Please log in to see expenses.</p>';
            if(pastExpensesContainer) pastExpensesContainer.innerHTML = '';
            return;
        }

        try {
            const response = await fetch('/expenses', {
                headers: { 'Authorization': 'Bearer ' + authToken }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const expenses = await response.json();

            if (recentSubmissionsContainer) {
                recentSubmissionsContainer.innerHTML = ''; // Clear static content
                // Display first 3 as recent, or customize as needed
                expenses.slice(0, 3).forEach(expense => {
                    recentSubmissionsContainer.innerHTML += createExpenseItemHTML(expense);
                });
                if (expenses.length === 0) {
                    recentSubmissionsContainer.innerHTML = '<p class="px-4 text-gray-500">No recent submissions found.</p>';
                }
            }

            if (pastExpensesContainer) {
                pastExpensesContainer.innerHTML = ''; // Clear static content
                // Display the rest (or all if no separate recent) as past
                expenses.forEach(expense => { // Or expenses.slice(3) if recent is separate
                    pastExpensesContainer.innerHTML += createExpenseItemHTML(expense);
                });
                 if (expenses.length === 0 && recentSubmissionsContainer.innerHTML.includes('No recent submissions')) {
                    // Only show if no expenses at all
                } else if (expenses.length === 0) {
                     pastExpensesContainer.innerHTML = '<p class="px-4 text-gray-500">No past expenses found.</p>';
                }
            }

        } catch (error) {
            console.error('Error fetching expenses:', error);
            if(recentSubmissionsContainer) recentSubmissionsContainer.innerHTML = `<p class="px-4 text-red-500">Error loading expenses: ${error.message}</p>`;
        }
    };

    // Event Listeners
    if (addExpenseButton) {
        addExpenseButton.addEventListener('click', () => {
            window.location.href = 'expenses.html'; // Navigate to the expense submission page
        });
    }

    if (searchButton && searchInput) {
        searchButton.addEventListener('click', () => {
            const searchTerm = searchInput.value;
            console.log('Search term:', searchTerm);
            // Placeholder: Implement search functionality (e.g., filter displayed expenses or call API)
            alert('Search functionality to be implemented. Searched for: ' + searchTerm);
        });
    }
    
    // Also allow search on Enter key press in input
    if (searchInput) {
        searchInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault(); // Prevent form submission if it's part of a form
                searchButton.click(); // Trigger the search button's click handler
            }
        });
    }


    if (categoryFilterButton) {
        categoryFilterButton.addEventListener('click', () => {
            console.log('Category filter clicked');
            alert('Category filter functionality to be implemented.');
        });
    }
    if (dateFilterButton) {
        dateFilterButton.addEventListener('click', () => {
            console.log('Date filter clicked');
            alert('Date filter functionality to be implemented.');
        });
    }
    if (statusFilterButton) {
        statusFilterButton.addEventListener('click', () => {
            console.log('Status filter clicked');
            alert('Status filter functionality to be implemented.');
        });
    }

    if (chatWithAIButton) {
        chatWithAIButton.addEventListener('click', () => {
            console.log('Chat with AI clicked');
            alert('Chat with AI functionality to be implemented.');
        });
    }

    // Initial load of expenses
    loadExpenses();
});
