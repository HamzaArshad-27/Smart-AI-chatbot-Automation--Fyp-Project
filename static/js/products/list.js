// Quick add to cart with smooth animation and toast notification
function quickAddToCart(productId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    const btn = event ? event.currentTarget : document.querySelector(`button[onclick*="${productId}"]`);
    if (!btn) return;
    
    const originalHtml = btn.innerHTML;
    
    // Add loading state
    btn.innerHTML = '<i class="fas fa-spinner fa-pulse"></i>';
    btn.disabled = true;
    
    // Simulate API call - replace with your actual fetch request
    setTimeout(() => {
        // Success state
        btn.innerHTML = '<i class="fas fa-check"></i>';
        
        // Show toast notification
        showToast('Item added to cart!', 'success');
        
        // Reset button after delay
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }, 1000);
    }, 500);
    
    // Example of actual API call (uncomment and modify as needed):
    /*
    fetch('/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ product_id: productId, quantity: 1 })
    })
    .then(response => response.json())
    .then(data => {
        btn.innerHTML = '<i class="fas fa-check"></i>';
        showToast('Item added to cart!', 'success');
        
        // Update cart count if you have one
        if (data.cart_count) {
            updateCartCount(data.cart_count);
        }
    })
    .catch(error => {
        btn.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
        showToast('Failed to add item', 'error');
    })
    .finally(() => {
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }, 1000);
    });
    */
}

// Toast notification function
function showToast(message, type = 'success') {
    // Remove existing toasts
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
    toast.innerHTML = `<i class="fas ${icon}"></i> ${message}`;
    
    document.body.appendChild(toast);
    
    // Remove after animation
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        toast.style.transition = 'all 0.3s ease-out';
        
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 2500);
}

// Sort select handler with proper URL management
document.addEventListener('DOMContentLoaded', function() {
    const sortSelect = document.getElementById('sortSelect');
    
    if (sortSelect) {
        sortSelect.addEventListener('change', function(e) {
            const url = new URL(window.location.href);
            url.searchParams.set('sort', e.target.value);
            url.searchParams.set('page', '1'); // Reset to first page when sorting changes
            window.location.href = url.toString();
        });
    }
    
    // Preserve sort parameter in price filter form
    const priceForm = document.getElementById('priceFilterForm');
    if (priceForm) {
        priceForm.addEventListener('submit', function(e) {
            const sortValue = document.getElementById('sortSelect')?.value;
            if (sortValue) {
                let sortInput = this.querySelector('input[name="sort"]');
                if (!sortInput) {
                    sortInput = document.createElement('input');
                    sortInput.type = 'hidden';
                    sortInput.name = 'sort';
                    this.appendChild(sortInput);
                }
                sortInput.value = sortValue;
            }
        });
    }
    
    // Lazy load images for better performance
    if ('loading' in HTMLImageElement.prototype) {
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
            img.src = img.dataset.src || img.src;
        });
    } else {
        // Fallback for browsers that don't support lazy loading
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
        document.body.appendChild(script);
    }
    
    // Debounced scroll handler for performance
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        if (scrollTimeout) {
            window.cancelAnimationFrame(scrollTimeout);
        }
        scrollTimeout = window.requestAnimationFrame(() => {
            // Add any scroll-based logic here if needed
            // Keeping this lightweight to prevent lag
        });
    }, { passive: true });
    
    // Active nav highlight
    const productNavLink = document.querySelector('a.nav-link[href*="products"]');
    if (productNavLink) {
        productNavLink.classList.add('active');
    }
});

// Helper function to get CSRF token (needed for POST requests)
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

// Update cart count (if you have a cart counter element)
function updateCartCount(count) {
    const cartCountElement = document.querySelector('.cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = count;
        cartCountElement.style.display = count > 0 ? 'inline-block' : 'none';
    }
}