from django import forms
from .models import Product, ProductReview, Category, ProductImage

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'description', 'short_description',
            'price', 'compare_price', 'cost_per_item', 'stock_quantity',
            'low_stock_threshold', 'sku', 'barcode', 'weight', 'dimensions',
            'is_active', 'is_featured', 'is_digital'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Wireless Headphones'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed product description...'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Brief description (Optional)...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'compare_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Original price (Optional)'}),
            'cost_per_item': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Cost per item (Optional)'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Default is 5'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if left blank'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional Barcode'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Weight in kg'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'L x W x H in cm'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_digital': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'sku': 'SKU (Optional)',
            'barcode': 'Barcode (Optional)',
            'low_stock_threshold': 'Low Stock Alert Threshold (Optional)',
            'compare_price': 'Compare at Price / Original Price (Optional)',
            'cost_per_item': 'Cost Per Item (Optional)',
            'weight': 'Weight (Optional)',
            'dimensions': 'Dimensions (Optional)',
            'short_description': 'Short Description (Optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sku'].required = False
        self.fields['low_stock_threshold'].required = False

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        compare_price = cleaned_data.get('compare_price')
        
        if compare_price and price and compare_price <= price:
            self.add_error('compare_price', 'Compare price (original price) must be greater than the sale price to apply a valid discount.')
            
        return cleaned_data

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_main', 'order']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Image description'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Stars') for i in range(1, 6)],
                attrs={'class': 'form-control'}
            ),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Review Title'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your review here...'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }