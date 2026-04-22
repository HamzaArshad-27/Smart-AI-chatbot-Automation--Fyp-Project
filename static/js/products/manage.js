let currentView = 'grid';
    
    // View Toggle
    function setView(view) {
        currentView = view;
        const gridView = document.getElementById('gridView');
        const listView = document.getElementById('listView');
        const gridBtn = document.getElementById('gridViewBtn');
        const listBtn = document.getElementById('listViewBtn');
        
        if (view === 'grid') {
            gridView.style.display = 'grid';
            listView.style.display = 'none';
            gridBtn.classList.add('active');
            listBtn.classList.remove('active');
            localStorage.setItem('productView', 'grid');
        } else {
            gridView.style.display = 'none';
            listView.style.display = 'block';
            listBtn.classList.add('active');
            gridBtn.classList.remove('active');
            localStorage.setItem('productView', 'list');
        }
    }
    
    // Load saved view preference
    const savedView = localStorage.getItem('productView');
    if (savedView) {
        setView(savedView);
    }
    
    // Search and Filters
    function filterProducts() {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
        const categoryFilter = document.getElementById('categoryFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;
        const stockFilter = document.getElementById('stockFilter').value;
        
        const products = document.querySelectorAll('.product-card');
        
        products.forEach(product => {
            const name = product.dataset.productName || '';
            const category = product.dataset.category || '';
            const status = product.dataset.status || '';
            const stock = parseInt(product.dataset.stock || 0);
            
            let show = true;
            
            if (searchTerm && !name.includes(searchTerm)) show = false;
            if (categoryFilter && category !== categoryFilter) show = false;
            if (statusFilter === 'active' && status !== 'active') show = false;
            if (statusFilter === 'inactive' && status !== 'inactive') show = false;
            if (stockFilter === 'low' && stock > 10) show = false;
            if (stockFilter === 'out' && stock > 0) show = false;
            if (stockFilter === 'in' && stock === 0) show = false;
            
            product.style.display = show ? 'block' : 'none';
        });
    }
    
    document.getElementById('searchInput')?.addEventListener('keyup', filterProducts);
    document.getElementById('categoryFilter')?.addEventListener('change', filterProducts);
    document.getElementById('statusFilter')?.addEventListener('change', filterProducts);
    document.getElementById('stockFilter')?.addEventListener('change', filterProducts);
    
    function resetFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('categoryFilter').value = '';
        document.getElementById('statusFilter').value = '';
        document.getElementById('stockFilter').value = '';
        filterProducts();
    }
    
    // Bulk Actions
    let selectedProducts = [];
    
    function updateBulkActions() {
        const checkboxes = document.querySelectorAll('.product-checkbox:checked');
        selectedProducts = Array.from(checkboxes).map(cb => cb.value);
        
        const bulkActions = document.getElementById('bulkActions');
        const selectedCount = document.getElementById('selectedCount');
        const deleteBtn = document.getElementById('deleteSelectedBtn');
        
        if (selectedProducts.length > 0) {
            bulkActions.classList.add('show');
            selectedCount.innerText = selectedProducts.length;
            deleteBtn.style.display = 'inline-block';
        } else {
            bulkActions.classList.remove('show');
            deleteBtn.style.display = 'none';
        }
    }
    
    function updateBulkActionsList() {
        const checkboxes = document.querySelectorAll('.product-checkbox-list:checked');
        selectedProducts = Array.from(checkboxes).map(cb => cb.value);
        
        const bulkActions = document.getElementById('bulkActions');
        const selectedCount = document.getElementById('selectedCount');
        
        if (selectedProducts.length > 0) {
            bulkActions.classList.add('show');
            selectedCount.innerText = selectedProducts.length;
        } else {
            bulkActions.classList.remove('show');
        }
    }
    
    function toggleSelectAllList() {
        const selectAll = document.getElementById('selectAllList');
        const checkboxes = document.querySelectorAll('.product-checkbox-list');
        checkboxes.forEach(cb => cb.checked = selectAll.checked);
        updateBulkActionsList();
    }
    
    function clearSelection() {
        document.querySelectorAll('.product-checkbox, .product-checkbox-list').forEach(cb => cb.checked = false);
        updateBulkActions();
        updateBulkActionsList();
    }
    
    function bulkActivate() {
        if (selectedProducts.length === 0) return;
        if (confirm(`Activate ${selectedProducts.length} product(s)?`)) {
            // Implement bulk activation via AJAX
            fetch('/products/bulk-activate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({product_ids: selectedProducts})
            }).then(() => location.reload());
        }
    }
    
    function bulkDeactivate() {
        if (selectedProducts.length === 0) return;
        if (confirm(`Deactivate ${selectedProducts.length} product(s)?`)) {
            fetch('/products/bulk-deactivate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({product_ids: selectedProducts})
            }).then(() => location.reload());
        }
    }
    
    function bulkDelete() {
        if (selectedProducts.length === 0) return;
        if (confirm(`⚠️ Delete ${selectedProducts.length} product(s)? This action cannot be undone!`)) {
            fetch('/products/bulk-delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({product_ids: selectedProducts})
            }).then(() => location.reload());
        }
    }
    
    function deleteProduct(productId) {
        if (confirm('Delete this product? This action cannot be undone!')) {
            window.location.href = `/products/delete/${productId}/`;
        }
    }
    
    function deleteSelected() {
        bulkDelete();
    }
    
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