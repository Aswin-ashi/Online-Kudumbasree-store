from django.db import models

# Create your models here.

# --- Customer / user Model ---

class Customer(models.Model):
    """Stores customer details."""
    name = models.CharField(max_length=30)
    username = models.CharField(max_length=25, unique=True)
    password = models.CharField(max_length=25)
    address = models.CharField(max_length=60)
    email = models.EmailField(unique=True) 
    phone = models.CharField(max_length=20)
    age = models.IntegerField()
    photo = models.ImageField(upload_to='customer_photos/')

    def __str__(self):
        return self.name

# --- Seller / Unit member Model ---

class Seller(models.Model):
    """Stores seller details, including an approval status."""
    name = models.CharField(max_length=30)
    username = models.CharField(max_length=25, unique=True)
    password = models.CharField(max_length=25)
    address = models.CharField(max_length=60)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    kudumbasree_details = models.CharField(max_length=90)
    passbook = models.ImageField(upload_to='seller_passbooks/')
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name

# --- Product model ---

class Product(models.Model):
    """Stores product details, linked to a seller."""
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.CharField(max_length=50, default='General') 
    photo = models.ImageField(upload_to='product_photos/')

    def __str__(self):
        return self.product_name

# --- Order model ---

class Order(models.Model):
    """Stores order details, linked to a customer and a product."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Order #{self.id} by {self.customer.name}"

class Feedback(models.Model):
    """Stores feedback from customers about sellers."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    feedback_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.customer.name} to {self.seller.name}"