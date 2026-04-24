// Image preview functionality
    const imageInput = document.getElementById('imageInput');
    const imagePreviewGrid = document.getElementById('imagePreviewGrid');
    let uploadedFiles = [];
    
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const files = Array.from(e.target.files);
            uploadedFiles = [...uploadedFiles, ...files];
            displayImagePreviews();
        });
    }
    
    function displayImagePreviews() {
        if (!imagePreviewGrid) return;
        
        imagePreviewGrid.innerHTML = '';
        uploadedFiles.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = function(event) {
                const previewItem = document.createElement('div');
                previewItem.className = 'image-preview-item';
                previewItem.innerHTML = `
                    <img src="${event.target.result}" alt="Preview">
                    <div class="image-actions">
                        <button type="button" class="btn btn-sm btn-danger" onclick="removeImage(${index})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                    ${index === 0 ? '<span class="main-badge">Main</span>' : ''}
                `;
                imagePreviewGrid.appendChild(previewItem);
            };
            reader.readAsDataURL(file);
        });
    }
    
    function removeImage(index) {
        uploadedFiles.splice(index, 1);
        const newFileList = new DataTransfer();
        uploadedFiles.forEach(file => newFileList.items.add(file));
        imageInput.files = newFileList.files;
        displayImagePreviews();
    }
    
    function deleteImage(imageId) {
        if (confirm('Delete this image?')) {
            fetch(`/products/delete-image/${imageId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            }).then(() => location.reload());
        }
    }
    
    // Price validation
    const priceInput = document.querySelector('#id_price');
    const comparePriceInput = document.querySelector('#id_compare_price');
    
    if (priceInput && comparePriceInput) {
        comparePriceInput.addEventListener('change', function() {
            const price = parseFloat(priceInput.value);
            const comparePrice = parseFloat(this.value);
            if (comparePrice && price && comparePrice <= price) {
                this.classList.add('is-invalid');
                showNotification('Compare price should be greater than regular price', 'warning');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }
    
    // Stock validation
    const stockInput = document.querySelector('#id_stock_quantity');
    const thresholdInput = document.querySelector('#id_low_stock_threshold');
    
    if (stockInput && thresholdInput) {
        thresholdInput.addEventListener('change', function() {
            const threshold = parseInt(this.value);
            if (threshold < 0) {
                this.classList.add('is-invalid');
                showNotification('Low stock threshold cannot be negative', 'warning');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }
    
    // Form submission with loading state
    const form = document.getElementById('productForm');
    const submitBtn = document.getElementById('submitBtn');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            submitBtn.classList.add('btn-loading');
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            submitBtn.disabled = true;
        });
    }
    
    // Save and add another
    function saveAndAddAnother() {
        const form = document.getElementById('productForm');
        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = 'save_and_add';
        form.appendChild(actionInput);
        form.submit();
    }
    
    // Notification system
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        notification.style.zIndex = '9999';
        notification.style.animation = 'slideDown 0.5s ease';
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'} me-2"></i>
                <div>${message}</div>
            </div>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // Auto-save draft (optional)
    let autoSaveTimeout;
    const formInputs = document.querySelectorAll('#productForm input, #productForm select, #productForm textarea');
    
    formInputs.forEach(input => {
        input.addEventListener('input', function() {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                // Implement auto-save functionality here
                console.log('Auto-saving draft...');
            }, 3000);
        });
    });
    
    // Get CSRF token
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
    
    // Character counter for description
    const descriptionField = document.querySelector('#id_description');
    if (descriptionField) {
        const counter = document.createElement('small');
        counter.className = 'text-muted float-end';
        counter.innerHTML = '0 characters';
        descriptionField.parentNode.appendChild(counter);
        
        descriptionField.addEventListener('input', function() {
            const count = this.value.length;
            counter.innerHTML = `${count} characters`;
            if (count > 5000) {
                counter.classList.add('text-danger');
            } else {
                counter.classList.remove('text-danger');
            }
        });
    }
    
    // Slug auto-generation (if name field exists)
    const nameField = document.querySelector('#id_name');
    const slugField = document.querySelector('#id_slug');
    
    if (nameField && slugField && !slugField.value) {
        nameField.addEventListener('blur', function() {
            const slug = this.value.toLowerCase()
                .replace(/[^\w\s-]/g, '')
                .replace(/\s+/g, '-')
                .replace(/--+/g, '-')
                .trim();
            slugField.value = slug;
        });
    }