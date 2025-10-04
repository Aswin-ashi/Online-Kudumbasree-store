import os
from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer, Seller, Order, Product, Feedback
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password 

# --- User Facing Views ---


def register_customer(request):
    """Handles the logic for registering a new customer."""
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        photo = request.FILES.get('photo')

        if Customer.objects.filter(username=username).exists() or Seller.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
            return redirect('register/customer/')

        # Hash the password for security before saving
        hashed_password = make_password(password)
        
        customer = Customer(
            name=name,
            username=username,
            password=hashed_password,
            address=address,
            phone=phone,
            age=age,
            photo=photo
        )
        customer.save()

        messages.success(request, 'Customer registration successful! Please log in.')
        return redirect('login')
    
    return render(request, 'login.html')

def register_seller(request):
    """Handles the logic for registering a new seller, setting them as pending approval."""
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        kudumbasree_details = request.POST.get('kudumbasree_details')
        passbook = request.FILES.get('passbook')

        if Seller.objects.filter(username=username).exists() or Customer.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
            return redirect('register/seller/')

        # Hash the password for security before saving
        hashed_password = make_password(password)

        seller = Seller(
            name=name,
            username=username,
            password=hashed_password,
            address=address,
            phone=phone,
            kudumbasree_details=kudumbasree_details,
            passbook=passbook,
            is_approved=False  # Set approval status to False by default
        )
        seller.save()

        messages.success(request, 'Seller registration request submitted! An admin will review your application.')
        return redirect('login')

    return render(request, 'login.html')


def login_view(request):
    """Handles the login logic for both customers and approved sellers."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if it's an admin login
        if username == 'admin' and password == 'adminpass': # Replace with a secure admin check
             request.session['user_type'] = 'admin'
             return redirect('admin_dashboard')

        # Check for customer
        try:
            customer = Customer.objects.get(username=username)
            if check_password(password, customer.password):
                request.session['user_id'] = customer.id
                request.session['username'] = customer.username
                request.session['user_type'] = 'customer'
                messages.success(request, f'Welcome back, {customer.name}!')
                return redirect('customer_dashboard') # Redirect to a customer dashboard
        except Customer.DoesNotExist:
            pass # Continue to check for a seller

        # Check for an approved seller
        try:
            seller = Seller.objects.get(username=username, is_approved=True)
            if check_password(password, seller.password):
                request.session['user_id'] = seller.id
                request.session['username'] = seller.username
                request.session['user_type'] = 'seller'
                messages.success(request, f'Welcome back, {seller.name}!')
                return redirect('seller_dashboard') # Redirect to a seller dashboard
        except Seller.DoesNotExist:
            pass # User does not exist or is not approved

        messages.error(request, 'Invalid username, password, or seller account not approved.')
        return redirect('login')
        
    return render(request, 'login.html')


def logout_view(request):
    """Clears the session to log the user out."""
    request.session.flush()
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')


# --- Admin Panel Views ---

def admin_dashboard(request):
    """Displays the admin panel with lists of users."""
    # Add a check here to ensure only admins can access
    if request.session.get('user_type') != 'admin':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('login')
        
    customers = Customer.objects.all()
    approved_sellers = Seller.objects.filter(is_approved=True)
    pending_sellers = Seller.objects.filter(is_approved=False)
    
    context = {
        'customers': customers,
        'approved_sellers': approved_sellers,
        'pending_sellers': pending_sellers
    }
    return render(request, 'adminpanel.html', context)

def delete_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    customer.delete()
    messages.success(request, f'Customer "{customer.name}" has been deleted.')
    return redirect('admin_dashboard')

def delete_seller(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)
    seller.delete()
    messages.success(request, f'Seller "{seller.name}" has been deleted.')
    return redirect('admin_dashboard')

def approve_seller(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)
    seller.is_approved = True
    seller.save()
    messages.success(request, f'Seller "{seller.name}" has been approved.')
    return redirect('admin_dashboard')

def reject_seller(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)
    seller.delete() # Rejection means deleting the request
    messages.warning(request, f'The registration request for "{seller.name}" has been rejected.')
    return redirect('admin_dashboard')

# --- Seller Dashboard Views ---

def seller_dashboard(request):
    """Displays the seller dashboard with their products, orders, and feedback."""
    if request.session.get('user_type') != 'seller':
        messages.error(request, "You must be logged in as a seller to view this page.")
        return redirect('signup_login_page')

    seller = get_object_or_404(Seller, id=request.session['user_id'])
    products = Product.objects.filter(seller=seller)
    orders = Order.objects.filter(product__seller=seller)
    feedbacks = Feedback.objects.filter(seller=seller)

    context = {
        'seller': seller,
        'products': products,
        'orders': orders,
        'feedbacks': feedbacks,
    }
    return render(request, 'seller_dashboard.html', context)

def add_product(request):
    """Handles the form submission for adding a new product."""
    if request.method == 'POST':
        if request.session.get('user_type') != 'seller':
            return redirect('signup_login_page')

        seller = get_object_or_404(Seller, id=request.session['user_id'])
        
        Product.objects.create(
            seller=seller,
            product_name=request.POST.get('product_name'),
            price=request.POST.get('price'),
            stock=request.POST.get('stock'),
            description=request.POST.get('description'),
            category=request.POST.get('category'),
            photo=request.FILES.get('photo')
        )
        messages.success(request, 'Product added successfully!')
    return redirect('seller_dashboard')

def update_product(request, product_id):
    """Handles the form submission for updating an existing product."""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        if product.seller.id != request.session.get('user_id'):
            messages.error(request, "You are not authorized to edit this product.")
            return redirect('seller_dashboard')

        product.product_name = request.POST.get('product_name', product.product_name)
        product.price = request.POST.get('price', product.price)
        product.stock = request.POST.get('stock', product.stock)
        product.description = request.POST.get('description', product.description)
        product.category = request.POST.get('category', product.category)
        if request.FILES.get('photo'):
            product.photo = request.FILES.get('photo')
        
        product.save()
        messages.success(request, 'Product updated successfully!')
    return redirect('seller_dashboard')

def delete_product(request, product_id):
    """Deletes a product."""
    product = get_object_or_404(Product, id=product_id)
    if product.seller.id != request.session.get('user_id'):
        messages.error(request, "You are not authorized to delete this product.")
    else:
        product.delete()
        messages.success(request, 'Product deleted successfully.')
    return redirect('seller_dashboard')



def confirm_order(request, order_id):
    """Marks an order as confirmed."""
    order = get_object_or_404(Order, id=order_id)
    if order.product.seller.id != request.session.get('user_id'):
        messages.error(request, "Authorization error.")
    else:
        order.is_confirmed = True
        order.save()
        messages.success(request, f'Order #{order.id} has been confirmed.')
    return redirect('seller_dashboard')

def delete_order(request, order_id):
    """Deletes an order."""
    order = get_object_or_404(Order, id=order_id)
    if order.product.seller.id != request.session.get('user_id'):
        messages.error(request, "Authorization error.")
    else:
        order.delete()
        messages.warning(request, f'Order #{order.id} has been deleted.')
    return redirect('seller_dashboard')

def delete_feedback(request, feedback_id):
    """Deletes a feedback message."""
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if feedback.seller.id != request.session.get('user_id'):
        messages.error(request, "Authorization error.")
    else:
        feedback.delete()
        messages.info(request, 'Feedback has been deleted.')
    return redirect('seller_dashboard')




#--- Customer Dashboard ---

def customer_dashboard(request):
    return render(request,'index.html')
# --- Shop Page View ---

def shop_page(request):
    """Displays all products from approved sellers for customers to browse."""
    products = Product.objects.filter(seller__is_approved=True)
    return render(request, 'shop.html', {'products': products})