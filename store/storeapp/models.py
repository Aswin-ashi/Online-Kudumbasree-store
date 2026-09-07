from django.db import models

# --- Customer / user Model ---

class Customer(models.Model):
    """Stores customer details."""
    name = models.CharField(max_length=30)
    username = models.CharField(max_length=25, unique=True)
    password = models.CharField(max_length=128) 
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
    password = models.CharField(max_length=128) # Increased size for hashed passwords
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
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0) # ADDED: To calculate profit
    stock = models.IntegerField()
    category = models.CharField(max_length=50, default='General') 
    photo = models.ImageField(upload_to='product_photos/')

    def __str__(self):
        return self.product_name

# --- CartItem model ---

class CartItem(models.Model):
    """Represents an item in a user's shopping cart."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE) # Linked to your Customer model
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} for {self.customer.name}"

    @property
    def total_price(self):
        return self.quantity * self.product.price

# --- Order Models ---


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    # Address details captured at the time of order
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"Order {self.id} by {self.customer.name}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2) # ADDED: To snapshot cost at time of sale

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name}"

class Payment(models.Model):
    """Stores details of a successful payment."""
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    razorpay_payment_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.razorpay_payment_id} for Order {self.order.id}"

# --- Community Post Model ---
class CommunityPost(models.Model):
    """Stores community posts created by the admin."""
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='community_posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post {self.id} on {self.created_at.date()}"

class Feedback(models.Model):
    """Stores feedback from customers about sellers."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    feedback_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.customer.name} to {self.seller.name}"

