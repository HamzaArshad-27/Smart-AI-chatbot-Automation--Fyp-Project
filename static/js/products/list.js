function quickAddToCart(productId) {
        // Show a subtle alert or simulate add-to-cart (you can replace with actual fetch call)
        const btn = event.currentTarget;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        setTimeout(() => {
            btn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
                btn.innerHTML = originalHtml;
            }, 800);
            // Bootstrap toast or simple alert
            const toastHtml = `
                <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 1100">
                    <div class="toast align-items-center text-white bg-success border-0 show" role="alert">
                        <div class="d-flex">
                            <div class="toast-body">
                                <i class="fas fa-cart-plus me-2"></i> Item added to cart!
                            </div>
                            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', toastHtml);
            setTimeout(() => {
                const lastToast = document.querySelector('.toast:last-child');
                if(lastToast) lastToast.remove();
            }, 2000);
        }, 400);
    }

    // sorting redirect
    document.getElementById('sortSelect')?.addEventListener('change', function(e) {
        let url = new URL(window.location.href);
        let sortValue = e.target.value;
        url.searchParams.set('sort', sortValue);
        // preserve existing filters
        const minPrice = new URLSearchParams(window.location.search).get('min_price');
        const maxPrice = new URLSearchParams(window.location.search).get('max_price');
        const q = new URLSearchParams(window.location.search).get('q');
        if(minPrice) url.searchParams.set('min_price', minPrice);
        if(maxPrice) url.searchParams.set('max_price', maxPrice);
        if(q) url.searchParams.set('q', q);
        // reset page when sort changes
        url.searchParams.set('page', '1');
        window.location.href = url.toString();
    });

    // preserve sort in price filter form
    const priceForm = document.getElementById('priceFilterForm');
    if(priceForm) {
        priceForm.addEventListener('submit', function() {
            let sortSelect = document.getElementById('sortSelect');
            if(sortSelect && sortSelect.value) {
                let sortInput = document.createElement('input');
                sortInput.type = 'hidden';
                sortInput.name = 'sort';
                sortInput.value = sortSelect.value;
                this.appendChild(sortInput);
            }
        });
    }
    // active nav highlight for products page
    document.addEventListener('DOMContentLoaded', () => {
        const productNavLink = document.querySelector('a.nav-link[href*="products"]');
        if(productNavLink) productNavLink.classList.add('active');
    });