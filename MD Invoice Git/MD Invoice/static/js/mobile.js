// Mobile JavaScript for Invoice Generator

document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const mobileNavToggle = document.getElementById('mobileNavToggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobileNavOverlay');
    
    if (mobileNavToggle && sidebar && overlay) {
        mobileNavToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        });
        
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }
    
    // Close sidebar when clicking on nav links (mobile)
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 428) {
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
            }
        });
    });
    
    // Handle form submissions with loading states
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });
    
    // Touch-friendly table scrolling
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        let startX = 0;
        let scrollLeft = 0;
        
        table.addEventListener('touchstart', function(e) {
            startX = e.touches[0].pageX - table.offsetLeft;
            scrollLeft = table.scrollLeft;
        });
        
        table.addEventListener('touchmove', function(e) {
            e.preventDefault();
            const x = e.touches[0].pageX - table.offsetLeft;
            const walk = (x - startX) * 2;
            table.scrollLeft = scrollLeft - walk;
        });
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.classList.contains('show')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
    
    // Prevent zoom on input focus (iOS)
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        if (input.type !== 'range') {
            input.addEventListener('focus', function() {
                if (window.innerWidth <= 428) {
                    const viewport = document.querySelector('meta[name="viewport"]');
                    if (viewport) {
                        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
                    }
                }
            });
            
            input.addEventListener('blur', function() {
                const viewport = document.querySelector('meta[name="viewport"]');
                if (viewport) {
                    viewport.content = 'width=device-width, initial-scale=1.0';
                }
            });
        }
    });
});

// Utility functions
function showLoading(element) {
    if (element) {
        element.classList.add('loading');
        element.disabled = true;
    }
}

function hideLoading(element) {
    if (element) {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to page
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1070';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove after hide
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// AJAX helper functions
function makeRequest(url, options = {}) {
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
    
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    // Add CSRF token to headers if available
    if (csrfToken) {
        defaultOptions.headers['X-CSRFToken'] = csrfToken;
    }
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                // Handle different HTTP status codes
                if (response.status === 401) {
                    showToast('Session expired. Please login again.', 'warning');
                    setTimeout(() => window.location.href = '/login', 2000);
                    throw new Error('Unauthorized');
                } else if (response.status === 403) {
                    showToast('Access denied.', 'danger');
                    throw new Error('Forbidden');
                } else if (response.status === 404) {
                    showToast('Resource not found.', 'warning');
                    throw new Error('Not Found');
                } else if (response.status >= 500) {
                    showToast('Server error. Please try again later.', 'danger');
                    throw new Error('Server Error');
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            if (!error.message.includes('Unauthorized') && !error.message.includes('Forbidden')) {
                showToast('Request failed. Please try again.', 'danger');
            }
            throw error;
        });
}

// Invoice item management
function addInvoiceItem(invoiceId, itemData) {
    return makeRequest(`/api/invoices/${invoiceId}/items`, {
        method: 'POST',
        body: JSON.stringify(itemData)
    });
}

function removeInvoiceItem(invoiceId, itemId) {
    return makeRequest(`/api/invoices/${invoiceId}/items/${itemId}`, {
        method: 'DELETE'
    });
}

function updateInvoiceStatus(invoiceId, status) {
    return makeRequest(`/api/invoices/${invoiceId}/status`, {
        method: 'POST',
        body: JSON.stringify({ status: status })
    });
}

function updateInvoiceSettings(invoiceId, settings) {
    return makeRequest(`/api/invoices/${invoiceId}/settings`, {
        method: 'POST',
        body: JSON.stringify(settings)
    });
}

// Format currency for display
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for global use
window.InvoiceApp = {
    showLoading,
    hideLoading,
    showToast,
    makeRequest,
    addInvoiceItem,
    removeInvoiceItem,
    updateInvoiceStatus,
    updateInvoiceSettings,
    formatCurrency,
    formatDate,
    debounce
};
