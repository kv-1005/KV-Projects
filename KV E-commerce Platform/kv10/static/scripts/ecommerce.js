// KV Store - E-commerce JavaScript
// Interactive functionality for the black and green themed store

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functionality
    initMobileMenu();
    initSearchSuggestions();
    initCartFunctionality();
    initProductActions();
    initSmoothScrolling();
    initAnimations();
    initFormValidation();
    initMessages();
    initBackToTop();
});

// Initialize messages
function initMessages() {
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => {
        const closeBtn = message.querySelector('.message-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                message.remove();
            });
        }
        
        // Auto-remove messages after 5 seconds
        setTimeout(() => {
            if (message.parentNode) {
                message.style.opacity = '0';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.remove();
                    }
                }, 300);
            }
        }, 5000);
    });
}

// Mobile Menu Functionality
function initMobileMenu() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            mobileMenuToggle.classList.toggle('active');
        });
    }
}

// Search Suggestions
function initSearchSuggestions() {
    const searchInput = document.querySelector('.search-input');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            hideSearchSuggestions();
            return;
        }
        
        searchTimeout = setTimeout(() => {
            fetchSearchSuggestions(query);
        }, 300);
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.nav-search')) {
            hideSearchSuggestions();
        }
    });
}

// Hide search suggestions
function hideSearchSuggestions() {
    const dropdown = document.querySelector('.search-suggestions-dropdown');
    if (dropdown) {
        dropdown.style.display = 'none';
    }
}

// Fetch search suggestions from backend
function fetchSearchSuggestions(query) {
    fetch(`/api/search-suggestions/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchSuggestions(data.suggestions);
        })
        .catch(error => {
            console.log('Search suggestions not available');
        });
}

// Display search suggestions
function displaySearchSuggestions(suggestions) {
    let dropdown = document.querySelector('.search-suggestions-dropdown');
    if (!dropdown) {
        const searchContainer = document.querySelector('.nav-search');
        if (searchContainer) {
            dropdown = document.createElement('div');
            dropdown.className = 'search-suggestions-dropdown';
            searchContainer.appendChild(dropdown);
        }
    }
    
    if (dropdown) {
        if (suggestions && suggestions.length > 0) {
            dropdown.innerHTML = suggestions.map(suggestion => 
                `<div class="suggestion-item">${suggestion}</div>`
            ).join('');
            dropdown.style.display = 'block';
            
            // Add click handlers
            dropdown.querySelectorAll('.suggestion-item').forEach(item => {
                item.addEventListener('click', function() {
                    const searchInput = document.querySelector('.search-input');
                    if (searchInput) {
                        searchInput.value = this.textContent;
                        searchInput.form.submit();
                    }
                });
            });
        } else {
            dropdown.style.display = 'none';
        }
    }
}

// Cart Functionality
function initCartFunctionality() {
    // Add to cart with AJAX
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const productId = this.querySelector('.add-to-cart-btn')?.dataset.productId;
            
            if (productId) {
                addToCart(productId, formData);
            }
        });
    });
    
    // Update cart count
    updateCartCount();
}

// Add to cart with AJAX
function addToCart(productId, formData) {
    const button = document.querySelector(`[data-product-id="${productId}"]`);
    if (button) {
        button.classList.add('loading');
        button.disabled = true;
    }
    
    fetch(`/add-to-cart/${productId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => {
        if (response.redirected) {
            // If redirected, it means the user needs to login
            window.location.href = response.url;
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.success) {
            showNotification('Product added to cart!', 'success');
            updateCartCount();
        } else if (data) {
            showNotification(data.message || 'Failed to add to cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error adding to cart:', error);
        showNotification('Error adding to cart', 'error');
    })
    .finally(() => {
        if (button) {
            button.classList.remove('loading');
            button.disabled = false;
        }
    });
}

// Update cart count
function updateCartCount() {
    fetch('/api/cart-count/')
        .then(response => response.json())
        .then(data => {
            const cartCount = document.querySelector('.cart-count');
            if (cartCount) {
                cartCount.textContent = data.count;
                cartCount.style.display = data.count > 0 ? 'flex' : 'none';
            }
        })
        .catch(error => {
            console.log('Could not update cart count');
        });
}

// Product Actions
function initProductActions() {
    // Wishlist functionality
    const wishlistButtons = document.querySelectorAll('.add-to-wishlist-btn');
    wishlistButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            toggleWishlist(productId, this);
        });
    });
    
    // Quick view functionality
    const quickViewButtons = document.querySelectorAll('.quick-view-btn');
    quickViewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            openQuickView(productId);
        });
    });
}

// Toggle wishlist
function toggleWishlist(productId, button) {
    // Show loading state
    button.classList.add('loading');
    
    // Get CSRF token from cookie
    const csrftoken = getCookie('csrftoken');
    
    // Make the request with proper headers
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', csrftoken);
    
    fetch(`/add-to-wishlist/${productId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            button.classList.toggle('active', data.added);
            showNotification(data.message, 'success');
            
            // Update the heart icon based on the action
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = data.added ? 'fas fa-heart' : 'far fa-heart';
            }
            
            // Update wishlist count if the element exists
            const wishlistCount = document.querySelector('.wishlist-count');
            if (wishlistCount) {
                const currentCount = parseInt(wishlistCount.textContent) || 0;
                wishlistCount.textContent = data.added ? currentCount + 1 : Math.max(0, currentCount - 1);
            }
        } else {
            showNotification(data.message || 'Failed to update wishlist', 'error');
        }
    })
    .catch(error => {
        console.error('Wishlist error:', error);
        showNotification('Error connecting to server. Please try again.', 'error');
    })
    .finally(() => {
        // Remove loading state
        button.classList.remove('loading');
    });
}

// Quick view modal
function openQuickView(productId) {
    fetch(`/api/product/${productId}/quick-view/`)
        .then(response => response.json())
        .then(data => {
            showQuickViewModal(data);
        })
        .catch(error => {
            showNotification('Error loading product details', 'error');
        });
}

// Show quick view modal
function showQuickViewModal(productData) {
    const modal = document.createElement('div');
    modal.className = 'quick-view-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>${productData.name}</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="product-image">
                    <img src="${productData.image}" alt="${productData.name}">
                </div>
                <div class="product-info">
                    <p class="price">₹${productData.price}</p>
                    <p class="description">${productData.description}</p>
                    <button class="btn btn-primary add-to-cart-btn" data-product-id="${productData.id}">
                        Add to Cart
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal functionality
    modal.querySelector('.modal-close').addEventListener('click', () => {
        modal.remove();
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Smooth scrolling
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
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

// Animations
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    const animatedElements = document.querySelectorAll('.product-card, .category-card, .feature');
    animatedElements.forEach(el => {
        observer.observe(el);
    });
}

// Form validation
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

// Validate form
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showFieldError(input, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(input);
        }
        
        // Email validation
        if (input.type === 'email' && input.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(input.value)) {
                showFieldError(input, 'Please enter a valid email address');
                isValid = false;
            }
        }
        
        // Password validation
        if (input.type === 'password' && input.value) {
            if (input.value.length < 8) {
                showFieldError(input, 'Password must be at least 8 characters long');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

// Show field error
function showFieldError(input, message) {
    clearFieldError(input);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    input.parentNode.appendChild(errorDiv);
    input.classList.add('error');
}

// Clear field error
function clearFieldError(input) {
    const existingError = input.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    input.classList.remove('error');
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `message message-${type}`;
    notification.innerHTML = `
        ${message}
        <button class="message-close">&times;</button>
    `;
    
    const container = document.querySelector('.messages-container') || createMessagesContainer();
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
    
    // Close button functionality
    notification.querySelector('.message-close').addEventListener('click', () => {
        notification.remove();
    });
}

// Create messages container if it doesn't exist
function createMessagesContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}

// Get cookie value
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Lazy loading for images
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Theme toggle
function initThemeToggle() {
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });
    }
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
}

// Newsletter subscription
function initNewsletterSubscription() {
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('input[type="email"]').value;
            
            // Simulate newsletter subscription
            showNotification('Thank you for subscribing to our newsletter!', 'success');
            this.reset();
        });
    }
}

// Product gallery
function initProductGallery() {
    const thumbnails = document.querySelectorAll('.product-thumbnail');
    const mainImage = document.getElementById('main-image');
    
    if (thumbnails.length && mainImage) {
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                const imageUrl = this.dataset.image;
                if (imageUrl) {
                    mainImage.src = imageUrl;
                    thumbnails.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                }
            });
        });
    }
}

// Quantity selector
function initQuantitySelector() {
    const quantitySelectors = document.querySelectorAll('.quantity-selector');
    
    quantitySelectors.forEach(selector => {
        const minusBtn = selector.querySelector('.quantity-minus');
        const plusBtn = selector.querySelector('.quantity-plus');
        const input = selector.querySelector('.quantity-input');
        
        if (minusBtn && plusBtn && input) {
            minusBtn.addEventListener('click', () => {
                const currentValue = parseInt(input.value);
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                }
            });
            
            plusBtn.addEventListener('click', () => {
                const currentValue = parseInt(input.value);
                const maxValue = parseInt(input.dataset.max) || 99;
                if (currentValue < maxValue) {
                    input.value = currentValue + 1;
                }
            });
        }
    });
}

// Back to top button
function initBackToTop() {
    const backToTopBtn = document.createElement('button');
    backToTopBtn.className = 'back-to-top';
    backToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    document.body.appendChild(backToTopBtn);
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }
    });
    
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Initialize additional functionality
initLazyLoading();
initThemeToggle();
initNewsletterSubscription();
initProductGallery();
initQuantitySelector(); 