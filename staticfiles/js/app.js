# static/js/app.js
// Main JavaScript file for the leave management system

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize date pickers
    initializeDatePickers();
    
    // Auto-calculate days for leave application
    calculateLeaveDays();
    
    // Real-time form validation
    initializeFormValidation();
    
    // Smooth scrolling for anchor links
    initializeSmoothScrolling();
});

// Date picker initialization
function initializeDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    
    dateInputs.forEach(input => {
        if (input.name === 'start_date' || input.name === 'end_date') {
            input.min = today;
        }
    });
}

// Calculate leave days automatically
function calculateLeaveDays() {
    const startDateInput = document.getElementById('id_start_date');
    const endDateInput = document.getElementById('id_end_date');
    
    if (startDateInput && endDateInput) {
        function updateDays() {
            const startDate = new Date(startDateInput.value);
            const endDate = new Date(endDateInput.value);
            
            if (startDate && endDate && startDate <= endDate) {
                const timeDiff = endDate - startDate;
                const dayDiff = Math.ceil(timeDiff / (1000 * 60 * 60 * 24)) + 1;
                
                // Display calculated days
                let daysDisplay = document.getElementById('calculated-days');
                if (!daysDisplay) {
                    daysDisplay = document.createElement('div');
                    daysDisplay.id = 'calculated-days';
                    daysDisplay.className = 'alert alert-info mt-2';
                    endDateInput.parentNode.appendChild(daysDisplay);
                }
                daysDisplay.innerHTML = `<i class="fas fa-calendar-day me-2"></i>Total days: <strong>${dayDiff}</strong>`;
            }
        }
        
        startDateInput.addEventListener('change', updateDays);
        endDateInput.addEventListener('change', updateDays);
    }
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
    });
}

// Smooth scrolling
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Utility functions
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner mx-auto';
    spinner.id = 'loading-spinner';
    
    if (element) {
        element.appendChild(spinner);
    }
}

function hideLoading() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.remove();
    }
}

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1070';
    document.body.appendChild(container);
    return container;
}

// API helper functions
async function apiCall(url, options = {}) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        credentials: 'same-origin',
    };
    
    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showToast('An error occurred. Please try again.', 'danger');
        throw error;
    }
}

// Export functions for use in other scripts
window.LeaveManagement = {
    showLoading,
    hideLoading,
    showToast,
    apiCall
};