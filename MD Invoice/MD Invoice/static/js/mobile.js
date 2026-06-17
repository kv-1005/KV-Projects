// Mobile JavaScript for Invoice Generator

document.addEventListener('DOMContentLoaded', function () {
    // Mobile navigation toggle
    const mobileNavToggle = document.getElementById('mobileNavToggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobileNavOverlay');

    if (mobileNavToggle && sidebar && overlay) {
        mobileNavToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        });

        overlay.addEventListener('click', function () {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }

    // Close sidebar when clicking on nav links (mobile)
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function () {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
            }
        });
    });

    // Handle form submissions with loading states
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function () {
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

        table.addEventListener('touchstart', function (e) {
            startX = e.touches[0].pageX - table.offsetLeft;
            scrollLeft = table.scrollLeft;
        });

        table.addEventListener('touchmove', function (e) {
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
            input.addEventListener('focus', function () {
                if (window.innerWidth <= 768) {
                    const viewport = document.querySelector('meta[name="viewport"]');
                    if (viewport) {
                        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
                    }
                }
            });

            input.addEventListener('blur', function () {
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
    toast.addEventListener('hidden.bs.toast', function () {
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

// Offer item management
function addOfferItem(offerId, itemData) {
    return makeRequest(`/api/offers/${offerId}/items`, {
        method: 'POST',
        body: JSON.stringify(itemData)
    });
}

function removeOfferItem(offerId, itemId) {
    return makeRequest(`/api/offers/${offerId}/items/${itemId}`, {
        method: 'DELETE'
    });
}

function updateOfferStatus(offerId, status) {
    return makeRequest(`/api/offers/${offerId}/status`, {
        method: 'POST',
        body: JSON.stringify({ status: status })
    });
}

function updateOfferSettings(offerId, settings) {
    return makeRequest(`/api/offers/${offerId}/settings`, {
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



// ==========================================
// IMPORT ITEMS LOGIC
// ==========================================

let currentImportDocItems = [];

function initImportModal() {
    const modal = document.getElementById('importItemsModal');
    if (!modal) return;

    const searchInput = document.getElementById('importSearchInput');
    const docTypeSelect = document.getElementById('importDocType');
    const resultsContainer = document.getElementById('importSearchResults');
    const itemsPreview = document.getElementById('importItemsPreview');
    const importBtn = document.getElementById('confirmImportBtn');

    // Auto-focus search input when modal opens
    modal.addEventListener('shown.bs.modal', function () {
        searchInput.focus();
    });

    // Reset state when modal closes
    modal.addEventListener('hidden.bs.modal', function () {
        searchInput.value = '';
        resultsContainer.innerHTML = `
            <div class="text-center py-4 text-muted">
                <i class="fas fa-search fa-2x mb-2 opacity-50"></i>
                <p class="mb-0">Type to search for documents</p>
            </div>
        `;
        resultsContainer.classList.remove('d-none');
        itemsPreview.classList.add('d-none');
        importBtn.disabled = true;
        currentImportDocItems = [];
    });

    // Search Handler
    const handleSearch = debounce(function () {
        const query = searchInput.value.trim();
        const type = docTypeSelect.value;

        if (query.length < 2) return;

        resultsContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary" role="status"></div></div>';

        makeRequest(`/api/search-documents?type=${type}&q=${encodeURIComponent(query)}`)
            .then(data => {
                if (data.length === 0) {
                    resultsContainer.innerHTML = `
                        <div class="text-center py-4 text-muted">
                            <i class="fas fa-file-excel fa-2x mb-2 opacity-50"></i>
                            <p class="mb-0">No documents found</p>
                        </div>
                    `;
                    return;
                }

                let html = '';
                data.forEach(doc => {
                    html += `
                        <a href="#" class="list-group-item list-group-item-action import-doc-item" data-id="${doc.id}" onclick="selectImportDoc(${doc.id}, '${type}')">
                            <div class="d-flex w-100 justify-content-between">
                                <h6 class="mb-1 fw-bold text-primary">${doc.number}</h6>
                                <small class="text-muted">${doc.date}</small>
                            </div>
                            <p class="mb-1 text-truncate">${doc.party_name}</p>
                            <div class="d-flex justify-content-between align-items-center">
                                <small class="badge bg-light text-dark border">₹${formatCurrency(doc.total).replace('₹', '')}</small>
                                <small class="badge ${(doc.status === 'paid' || doc.status === 'approved') ? 'bg-success' : 'bg-secondary'}">${doc.status}</small>
                            </div>
                        </a>
                    `;
                });
                resultsContainer.innerHTML = html;
            })
            .catch(err => {
                resultsContainer.innerHTML = `<div class="text-center text-danger py-3">Error searching: ${err.message}</div>`;
            });
    }, 500);

    searchInput.addEventListener('input', handleSearch);
    docTypeSelect.addEventListener('change', handleSearch);

    // Import Button Handler
    importBtn.addEventListener('click', function () {
        const checkedBoxes = document.querySelectorAll('.import-item-checkbox:checked');
        if (checkedBoxes.length === 0) return;

        const selectedItems = Array.from(checkedBoxes).map(cb => {
            const index = parseInt(cb.dataset.index);
            return currentImportDocItems[index];
        });

        // Determine destination based on current page
        const currentDocId = window.invoiceData?.id || window.offerData?.id || window.poData?.id || window.challanData?.id;

        let addItemFunc = null;
        if (window.invoiceData) addItemFunc = window.InvoiceApp.addInvoiceItem;
        else if (window.offerData) addItemFunc = window.InvoiceApp.addOfferItem;
        else if (window.poData) addItemFunc = window.InvoiceApp.addPurchaseOrderItem;
        else if (window.challanData) addItemFunc = window.InvoiceApp.addDeliveryChallanItem;

        if (!currentDocId || !addItemFunc) {
            showToast('Error: Could not determine current document context', 'danger');
            return;
        }

        showLoading(importBtn);

        // Sequential import chain
        let promiseChain = Promise.resolve();
        let successCount = 0;

        selectedItems.forEach(item => {
            promiseChain = promiseChain.then(() => {
                return addItemFunc(currentDocId, item)
                    .then(() => successCount++)
                    .catch(err => console.error('Import item error:', err));
            });
        });

        promiseChain.then(() => {
            hideLoading(importBtn);
            const modalInstance = bootstrap.Modal.getInstance(modal);
            modalInstance.hide();

            showToast(`Successfully imported ${successCount} items`, 'success');

            // Refresh items list on page
            if (typeof updateItemsList === 'function') updateItemsList();
            setTimeout(() => window.location.reload(), 1000);
        });
    });
}

// Global function to be called from onclick in HTML
window.selectImportDoc = function (docId, type) {
    const resultsContainer = document.getElementById('importSearchResults');
    const itemsPreview = document.getElementById('importItemsPreview');
    const tableBody = document.getElementById('importItemsTableBody');
    const itemsLabel = document.getElementById('selectedDocLabel');
    const importBtn = document.getElementById('confirmImportBtn');

    resultsContainer.classList.add('d-none');
    itemsPreview.classList.remove('d-none');
    tableBody.innerHTML = '<tr><td colspan="4" class="text-center py-3"><div class="spinner-border spinner-border-sm text-primary"></div> Loading items...</td></tr>';

    makeRequest(`/api/get-document-items/${docId}?type=${type}`)
        .then(data => {
            if (!data.success) throw new Error(data.error || 'Failed to fetch items');

            currentImportDocItems = data.items;
            itemsLabel.textContent = `Items from ${data.doc_number}`;

            if (currentImportDocItems.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">No items found in this document</td></tr>';
                importBtn.disabled = true;
                return;
            }

            let html = '';
            currentImportDocItems.forEach((item, index) => {
                html += `
                    <tr>
                        <td class="ps-3">
                            <input class="form-check-input import-item-checkbox cursor-pointer" type="checkbox" data-index="${index}" checked>
                        </td>
                        <td>
                            <div class="fw-bold">${item.description}</div>
                            <small class="text-muted">HSN: ${item.hsn_code}</small>
                        </td>
                        <td class="text-center">${item.quantity}</td>
                        <td class="text-end pe-3 fw-bold">₹${formatCurrency(item.amount).replace('₹', '')}</td>
                    </tr>
                `;
            });
            tableBody.innerHTML = html;
            importBtn.disabled = false;

            // Setup Select All
            const selectAll = document.getElementById('selectAllImportItems');
            const checkboxes = document.querySelectorAll('.import-item-checkbox');

            selectAll.checked = true;
            selectAll.onclick = function () {
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            };

        })
        .catch(err => {
            tableBody.innerHTML = `<tr><td colspan="4" class="text-center text-danger py-3">Error: ${err.message}</td></tr>`;
        });
};

window.backToResults = function () {
    document.getElementById('importSearchResults').classList.remove('d-none');
    document.getElementById('importItemsPreview').classList.add('d-none');
};

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
    debounce,
    addOfferItem,
    removeOfferItem,
    updateOfferStatus,
    updateOfferSettings,
    initImportModal,
    addPurchaseOrderItem,
    addDeliveryChallanItem
};

function addPurchaseOrderItem(poId, itemData) {
    return makeRequest(`/api/purchase-orders/${poId}/items`, {
        method: 'POST',
        body: JSON.stringify(itemData)
    });
}

function addDeliveryChallanItem(dcId, itemData) {
    return makeRequest(`/api/delivery-challans/${dcId}/items`, {
        method: 'POST',
        body: JSON.stringify(itemData)
    });
}

