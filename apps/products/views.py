from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.utils.text import slugify
from .models import Product, Category, ProductReview, ProductImage
from .forms import ProductForm, ProductReviewForm, ProductImageForm

def product_list(request, category_slug=None):
    """Display list of products with filtering and search"""
    products = Product.objects.filter(is_active=True)
    
    # Category filter
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    else:
        category = None
    
    # Search filter
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    sort_options = {
        '-created_at': 'Latest',
        'price': 'Price: Low to High',
        '-price': 'Price: High to Low',
        'name': 'Name: A to Z',
        '-name': 'Name: Z to A',
        '-total_sold': 'Best Selling',
    }
    
    products = products.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    # Get all categories for sidebar
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'categories': categories,
        'current_category': category,
        'search_query': search_query,
        'sort_by': sort_by,
        'sort_options': sort_options,
    }
    
    return render(request, 'products/list.html', context)

def product_detail(request, slug):
    """Display product details"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.filter(is_approved=True)[:10]
    
    # Get average rating
    avg_rating = product.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Related products from same category
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Review form
    review_form = ProductReviewForm()
    
    context = {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'related_products': related_products,
        'review_form': review_form,
    }
    
    return render(request, 'products/detail.html', context)

@login_required
def add_review(request, slug):
    """Add a review for a product"""
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            
            # Update product average rating
            avg_rating = product.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg'] or 0
            product.average_rating = avg_rating
            product.total_reviews = product.reviews.filter(is_approved=True).count()
            product.save()
            
            messages.success(request, 'Review added successfully!')
            return redirect('products:detail', slug=product.slug)
    
    return redirect('products:detail', slug=product.slug)

# Product CRUD Views for Company
@login_required
def product_manage(request):
    """Manage products - for company and seller"""
    if request.user.role == 'company':
        products = Product.objects.filter(company=request.user.company_profile)
    elif request.user.role == 'seller':
        products = Product.objects.filter(seller=request.user.seller_profile)
    else:
        messages.error(request, 'You do not have permission to manage products')
        return redirect('dashboard:index')
    
    context = {
        'products': products.order_by('-created_at'),
        'total_products': products.count(),
    }
    return render(request, 'products/manage.html', context)

@login_required
def product_create(request):
    """Create new product"""
    print(f"User role: {request.user.role}")  # Debug print
    
    if request.user.role == 'company':
        try:
            company = request.user.company_profile
            seller = None
        except:
            messages.error(request, 'Company profile not found. Please contact support.')
            return redirect('dashboard:index')
    elif request.user.role == 'seller':
        try:
            seller = request.user.seller_profile
            company = seller.company
        except:
            messages.error(request, 'Seller profile not found. Please contact support.')
            return redirect('dashboard:index')
    else:
        messages.error(request, 'You do not have permission to add products')
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                product.company = company
                product.seller = seller
                product.slug = slugify(product.name)
                
                # Ensure unique slug
                original_slug = product.slug
                counter = 1
                while Product.objects.filter(slug=product.slug).exists():
                    product.slug = f"{original_slug}-{counter}"
                    counter += 1
                
                product.save()
                
                # Handle multiple images
                images = request.FILES.getlist('images')
                for i, image in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        image=image,
                        is_main=(i == 0),
                        order=i
                    )
                
                messages.success(request, f'Product "{product.name}" created successfully!')
                return redirect('products:manage')
            except Exception as e:
                messages.error(request, f'Error creating product: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
    
    # Get categories for form
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'categories': categories,
        'is_edit': False,
    }
    return render(request, 'products/form.html', context)

@login_required
def product_edit(request, product_id):
    """Edit existing product"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check permission
    if request.user.role == 'company' and product.company != request.user.company_profile:
        messages.error(request, 'You do not have permission to edit this product')
        return redirect('products:manage')
    elif request.user.role == 'seller' and product.seller != request.user.seller_profile:
        messages.error(request, 'You do not have permission to edit this product')
        return redirect('products:manage')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('products:manage')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'is_edit': True,
    }
    return render(request, 'products/form.html', context)

@login_required
def product_delete(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check permission
    if request.user.role == 'company' and product.company != request.user.company_profile:
        messages.error(request, 'You do not have permission to delete this product')
        return redirect('products:manage')
    elif request.user.role == 'seller' and product.seller != request.user.seller_profile:
        messages.error(request, 'You do not have permission to delete this product')
        return redirect('products:manage')
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('products:manage')
    
    return render(request, 'products/delete.html', {'product': product})

@login_required
def product_images(request, product_id):
    """Manage product images"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check permission
    if request.user.role == 'company' and product.company != request.user.company_profile:
        messages.error(request, 'You do not have permission to manage images for this product')
        return redirect('products:manage')
    
    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.product = product
            image.save()
            messages.success(request, 'Image added successfully!')
            return redirect('products:images', product_id=product.id)
    
    images = product.images.all()
    context = {
        'product': product,
        'images': images,
        'form': ProductImageForm(),
    }
    return render(request, 'products/images.html', context)

@login_required
def product_image_delete(request, image_id):
    """Delete product image"""
    image = get_object_or_404(ProductImage, id=image_id)
    product_id = image.product.id
    
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image deleted successfully!')
    
    return redirect('products:images', product_id=product_id)






####################################### Categoy ####################################
# Add these imports at the top
from .models import Product, Category, ProductReview, ProductImage
from .forms import ProductForm, ProductReviewForm, ProductImageForm, CategoryForm

# Category Management Views
@login_required
#@user_passes_test(lambda u: u.is_superuser or u.role == 'admin,company')
def category_list(request):
    """List all categories for admin"""
    categories = Category.objects.all()
    print("VIEW HIT")
    return render(request, 'products/categories/category_list.html', {'categories': categories})

@login_required
#@user_passes_test(lambda u: u.is_superuser or u.role == 'admin,company')
def category_create(request):
    """Create new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('products:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'products/categories/form.html', {'form': form, 'is_edit': False})

@login_required
#@user_passes_test(lambda u: u.is_superuser or u.role == 'admin,company')
def category_edit(request, category_id):
    """Edit category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('products:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'products/categories/form.html', {'form': form, 'category': category, 'is_edit': True})

@login_required
#@user_passes_test(lambda u: u.is_superuser or u.role == 'admin,company')
def category_delete(request, category_id):
    """Delete category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('products:category_list')
    
    return render(request, 'products/categories/delete.html', {'category': category})






import json
from django.http import JsonResponse



def api_products(request):
    """API endpoint for products with filtering"""
    products = Product.objects.filter(is_active=True)
    
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    # Search filter
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Order by
    products = products.order_by('-created_at')[:12]
    
    # Prepare data
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.price),
            'compare_price': float(product.compare_price) if product.compare_price else None,
            'discount_percentage': product.discount_percentage,
            'average_rating': float(product.average_rating) if product.average_rating else 0,
            'total_reviews': product.total_reviews,
            'image': product.images.first().image.url if product.images.first() else None,
        })
    
    return JsonResponse({
        'products': products_data,
        'total': len(products_data)
    })