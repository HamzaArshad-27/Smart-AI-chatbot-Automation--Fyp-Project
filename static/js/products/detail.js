// // Image gallery thumbnail switcher
//     function changeMainImage(src, element) {
//         document.getElementById('mainProductImage').src = src;
//         document.querySelectorAll('.thumbnail-img').forEach(thumb => {
//             thumb.classList.remove('active');
//         });
//         element.classList.add('active');
//     }

//     // Quantity selector logic
//     function updateQuantity(delta) {
//         let input = document.getElementById('quantityInput');
//         let currentVal = parseInt(input.value);
//         let min = parseInt(input.min) || 1;
//         let max = parseInt(input.max) || 999;
//         let newVal = currentVal + delta;
//         if (newVal >= min && newVal <= max) {
//             input.value = newVal;
//         }
//     }

//     // Prevent negative manual entry
//     document.getElementById('quantityInput')?.addEventListener('change', function(e) {
//         let val = parseInt(e.target.value);
//         let min = parseInt(e.target.min) || 1;
//         let max = parseInt(e.target.max) || 999;
//         if (isNaN(val) || val < min) e.target.value = min;
//         if (val > max) e.target.value = max;
//     });

//     // Go to cart page


//     // Show toast notification
//     function showToast(message, type = 'success') {
//         const toastHtml = `
//             <div class="toast-notification">
//                 <div class="bg-${type === 'success' ? 'success' : 'danger'} text-white p-3 rounded-4 shadow-lg d-flex align-items-center gap-3" style="min-width: 280px;">
//                     <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} fa-lg"></i>
//                     <span class="flex-grow-1">${message}</span>
//                     <button onclick="this.parentElement.parentElement.remove()" class="btn-close btn-close-white"></button>
//                 </div>
//             </div>
//         `;
//         document.body.insertAdjacentHTML('beforeend', toastHtml);
//         setTimeout(() => {
//             const toast = document.querySelector('.toast-notification');
//             if (toast) toast.remove();
//         }, 3000);
//     }

//     // Handle add to cart with AJAX for better UX (optional but keeps user on page)
//     const cartForm = document.getElementById('addToCartForm');
//     if(cartForm) {
//         cartForm.addEventListener('submit', async function(e) {
//             e.preventDefault(); // Prevent default form submission
            
//             const formData = new FormData(this);
//             const submitBtn = this.querySelector('button[type="submit"]');
//             const originalText = submitBtn.innerHTML;
            
//             // Show loading state
//             submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Adding...';
//             submitBtn.disabled = true;
            
//             try {
//                 const response = await fetch(this.action, {
//                     method: 'POST',
//                     body: formData,
//                     headers: {
//                         'X-Requested-With': 'XMLHttpRequest'
//                     }
//                 });
                
//                 const data = await response.json();
                
//                 if (data.success) {
//                     // Show success toast
//                     showToast(data.message || 'Product added to cart successfully!', 'success');
                    
//                     // Update cart badge in navbar
//                     const cartBadge = document.querySelector('.cart-badge-new');
//                     if (cartBadge && data.cart_count) {
//                         if (data.cart_count > 0) {
//                             cartBadge.textContent = data.cart_count;
//                             cartBadge.style.display = 'inline-flex';
//                         } else {
//                             cartBadge.style.display = 'none';
//                         }
//                     }
                    
//                     // Ask user if they want to go to cart or continue shopping
//                     setTimeout(() => {
//                         if (confirm('Product added to cart! Would you like to view your cart now?')) {
//                             window.location.href = "{% url 'cart:view' %}";
//                         }
//                     }, 500);
//                 } else {
//                     showToast(data.error || 'Failed to add product to cart', 'error');
//                 }
//             } catch (error) {
//                 console.error('Error:', error);
//                 showToast('Network error. Please try again.', 'error');
//             } finally {
//                 // Reset button
//                 submitBtn.innerHTML = originalText;
//                 submitBtn.disabled = false;
//             }
//         });
//     }