from django.db import models
from django.core.validators import FileExtensionValidator
from apps.accounts.models import User

from django.db import models
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.models import User
from django.utils.text import slugify

class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField()
    website = models.URLField(blank=True)
    tax_number = models.CharField(max_length=50, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'Companies'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def create_company_profile(sender, instance, created, **kwargs):
    """Create Company profile when a user with role 'company' is created"""
    if created and instance.role == 'company':
        Company.objects.create(
            user=instance,
            name=instance.email.split('@')[0],  # Default name from email
            email=instance.email,
            registration_number=f"REG{instance.id:06d}",
            is_active=instance.is_approved
        )
class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sellers')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sellers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.company.name}"