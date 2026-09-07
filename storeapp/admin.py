from django.contrib import admin
# Super user: okstore | pass: 1234
from .models import (
    Customer, Seller, Product, Order, OrderItem,
    CartItem, Payment, CommunityPost, Feedback
)

admin.site.register(Customer)
admin.site.register(Seller)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(CartItem)
admin.site.register(Payment)
admin.site.register(CommunityPost)
admin.site.register(Feedback)
