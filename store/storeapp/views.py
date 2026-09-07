import os
from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer, Seller, CartItem, Product, Feedback, Order, OrderItem, Payment, CommunityPost
from django.contrib import messages
from decimal import Decimal
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField
from django.db import transaction
from django.utils import timezone
import datetime


# --- Helper Functions ---
def get_logged_in_user(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')

    if user_type == 'admin':
        return 'admin', None

    if not user_id:
        return None, None

    if user_type == 'customer':
        try:
            return 'customer', Customer.objects.get(id=user_id)
        except Customer.DoesNotExist:
            return None, None
    elif user_type == 'seller':
        try:
            return 'seller', Seller.objects.get(id=user_id)
        except Seller.DoesNotExist:
            return None, None
    return None, None


def get_cart_context(customer):
    """Helper to get cart items and count for a logged-in customer."""
    if not customer:
        return {'cart_items': [], 'cart_item_count': 0, 'cart_product_ids': []}
    
    cart_items = CartItem.objects.filter(customer=customer)
    cart_item_count = sum(item.quantity for item in cart_items)
    cart_product_ids = list(cart_items.values_list('product_id', flat=True))
    
    return {
        'cart_items': cart_items,
        'cart_item_count': cart_item_count,
        'cart_product_ids': cart_product_ids,
    }


# --- Registration Views ---
def register_customer(request):
    if request.method == 'POST':
        # ... (registration logic remains the same)
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        photo = request.FILES.get('photo')

        if Customer.objects.filter(username=username).exists() or Seller.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
            return redirect('register_customer')

        Customer.objects.create(
            name=name,
            username=username,
            email=email,
            password=password,
            address=address,
            phone=phone,
            age=age,
            photo=photo
        )
        messages.success(request, 'Registration successful! Please log in.')
        return redirect('login')

    return render(request, 'login.html')



def register_seller(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        kudumbasree_details = request.POST.get('kudumbasree_details')
        passbook = request.FILES.get('passbook')

        if Seller.objects.filter(username=username).exists() or Customer.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
            return redirect('register_seller')
        
        if Seller.objects.filter(email=email).exists() or Customer.objects.filter(email=email).exists():
            messages.error(request, f'The email address "{email}" is already in use.')
            return redirect('register_seller')

        Seller.objects.create(
            name=name, username=username, password=password, address=address, email=email,
            phone=phone, kudumbasree_details=kudumbasree_details, passbook=passbook, is_approved=False
        )
        messages.success(request, 'Seller request submitted! Await admin approval.')
        return redirect('login')

    return render(request, 'login.html')


# --- Login / Logout ---
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # --- Admin Login ---
        if username == 'admin' and password == 'adminpass':
            request.session['user_type'] = 'admin'
            request.session['user_id'] = 0   # Add this line
            request.session.modified = True
            messages.success(request, 'Welcome Admin!')
            return redirect('admin_dashboard')

        # --- Customer Login ---
        try:
            customer = Customer.objects.get(username=username)
            if password == customer.password:
                request.session['user_type'] = 'customer'
                request.session['user_id'] = customer.id
                messages.success(request, f'Welcome {customer.name}!')
                return redirect('customer_dashboard')
        except Customer.DoesNotExist:
            pass

        # --- Seller Login ---
        try:
            seller = Seller.objects.get(username=username, is_approved=True)
            if password == seller.password:
                request.session['user_type'] = 'seller'
                request.session['user_id'] = seller.id
                messages.success(request, f'Welcome {seller.name}!')
                return redirect('seller_dashboard')
        except Seller.DoesNotExist:
            pass

        messages.error(request, 'Invalid credentials or seller not approved.')
        return redirect('login')

    return render(request, 'login.html')



def logout_view(request):
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('login')


# --- Admin Views ---
def admin_dashboard(request):
    user_type, _ = get_logged_in_user(request)
    if user_type != 'admin':
        messages.warning(request, "Admin access only.")
        return redirect('login')

    # --- Sales Report Logic ---
    current_time = timezone.now()
    selected_year = int(request.GET.get('year', current_time.year))
    selected_month = int(request.GET.get('month', current_time.month))

    # Base queryset for all calculations
    items_sold = OrderItem.objects.filter(
        order__created_at__year=selected_year,
        order__created_at__month=selected_month
    )

    # 1. Total Stats
    total_sales = items_sold.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
    total_cost = items_sold.aggregate(total=Sum(F('cost_price') * F('quantity')))['total'] or 0
    total_profit = total_sales - total_cost
    total_products_sold = items_sold.aggregate(total=Sum('quantity'))['total'] or 0

    # 2. Product-wise Stats
    product_sales = items_sold.values('product__product_name', 'product__seller__name').annotate(
        total_quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price')),
        total_cost=Sum(F('quantity') * F('cost_price'))
    ).annotate(
        total_profit=ExpressionWrapper(F('total_revenue') - F('total_cost'), output_field=DecimalField())
    ).order_by('-total_profit')

    # 3. Seller-wise Stats
    seller_sales = items_sold.values('product__seller__name').annotate(
        total_quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price')),
        total_cost=Sum(F('quantity') * F('cost_price'))
    ).annotate(
        total_profit=ExpressionWrapper(F('total_revenue') - F('total_cost'), output_field=DecimalField())
    ).order_by('-total_profit')

    # Data for filters
    years = range(2024, current_time.year + 1)
    months = [
        {"value": 1, "name": "January"}, {"value": 2, "name": "February"},
        {"value": 3, "name": "March"}, {"value": 4, "name": "April"},
        {"value": 5, "name": "May"}, {"value": 6, "name": "June"},
        {"value": 7, "name": "July"}, {"value": 8, "name": "August"},
        {"value": 9, "name": "September"}, {"value": 10, "name": "October"},
        {"value": 11, "name": "November"}, {"value": 12, "name": "December"}
    ]

    # --- Other Dashboard Data ---
    customers = Customer.objects.all()
    approved_sellers = Seller.objects.filter(is_approved=True)
    pending_sellers = Seller.objects.filter(is_approved=False)
    posts = CommunityPost.objects.all().order_by('-created_at')
    
    context = {
        'customers': customers,
        'approved_sellers': approved_sellers,
        'pending_sellers': pending_sellers,
        'posts': posts,
        'total_sales': total_sales,
        'total_profit': total_profit,
        'total_products_sold': total_products_sold,
        'product_sales': product_sales,
        'seller_sales': seller_sales,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'years': years,
        'months': months,
    }
    return render(request, 'adminpanel.html', context)



def delete_customer(request, customer_id):
    # ... (view logic remains the same)
    customer = get_object_or_404(Customer, id=customer_id)
    customer.delete()
    messages.success(request, f'Customer "{customer.name}" deleted.')
    return redirect('admin_dashboard')


def delete_seller(request, seller_id):
    # ... (view logic remains the same)
    seller = get_object_or_404(Seller, id=seller_id)
    seller.delete()
    messages.success(request, f'Seller "{seller.name}" deleted.')
    return redirect('admin_dashboard')


def approve_seller(request, seller_id):
    # ... (view logic remains the same)
    seller = get_object_or_404(Seller, id=seller_id)
    seller.is_approved = True
    seller.save()
    messages.success(request, f'Seller "{seller.name}" approved.')
    return redirect('admin_dashboard')


def reject_seller(request, seller_id):
    # ... (view logic remains the same)
    seller = get_object_or_404(Seller, id=seller_id)
    seller.delete()
    messages.warning(request, f'Seller "{seller.name}" rejected.')
    return redirect('admin_dashboard')

def add_post(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        image = request.FILES.get('image')

        # Validate that at least one field is provided
        if not description and not image:
            messages.error(request, "You must provide a description, an image, or both.")
            return redirect('admin_dashboard')

        CommunityPost.objects.create(description=description, image=image)
        messages.success(request, "Community post created successfully.")
    return redirect('admin_dashboard')

def update_post(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)

    if request.method == "POST":
        description = request.POST.get('description', '')
        if 'image' in request.FILES:
            post.image = request.FILES['image']
        post.description = description
        post.save()
        messages.success(request, "Post updated successfully.")
        return redirect('admin_dashboard')

    return redirect('admin_dashboard')

def delete_post(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    post.delete()
    messages.success(request, "Post deleted successfully.")
    return redirect('admin_dashboard')


# --- Seller Views ---
def seller_dashboard(request):
    user_type, seller = get_logged_in_user(request)
    if user_type != 'seller':
        messages.warning(request, "Seller login required.")
        return redirect('login')

    products = Product.objects.filter(seller=seller)
    orders = Order.objects.filter(items__product__seller=seller).distinct().order_by('-created_at')
    feedbacks = Feedback.objects.filter(seller=seller).order_by('-created_at')

    context = {
        'seller': seller,
        'products': products,
        'orders': orders,
        'feedbacks': feedbacks
    }
    return render(request, 'seller_dashboard.html', context)


def add_product(request):
    # ... (view logic remains the same)
    user_type, seller = get_logged_in_user(request)
    if user_type != 'seller' or request.method != 'POST':
        messages.warning(request, "Action requires seller login.")
        return redirect('products_page')

    Product.objects.create(
        seller=seller,
        product_name=request.POST.get('product_name'),
        price=request.POST.get('price'),
        stock=request.POST.get('stock'),
        description=request.POST.get('description'),
        category=request.POST.get('category'),
        photo=request.FILES.get('photo')
    )
    messages.success(request, "Product added successfully!")
    return redirect('seller_dashboard')


def update_product(request, product_id):
    # ... (view logic remains the same)
    user_type, seller = get_logged_in_user(request)
    product = get_object_or_404(Product, id=product_id)
    if product.seller != seller or request.method != 'POST':
        messages.warning(request, "Not authorized.")
        return redirect('products_page')

    product.product_name = request.POST.get('product_name', product.product_name)
    product.price = request.POST.get('price', product.price)
    product.stock = request.POST.get('stock', product.stock)
    product.description = request.POST.get('description', product.description)
    product.category = request.POST.get('category', product.category)
    if request.FILES.get('photo'):
        product.photo = request.FILES.get('photo')
    product.save()
    messages.success(request, "Product updated successfully!")
    return redirect('seller_dashboard')


def delete_product(request, product_id):
    user_type, seller = get_logged_in_user(request)
    product = get_object_or_404(Product, id=product_id)
    if product.seller != seller:
        messages.warning(request, "Not authorized.")
    else:
        product.delete()
        messages.success(request, "Product deleted.")
    return redirect('seller_dashboard')

def confirm_order(request, order_id):
    user_type, seller = get_logged_in_user(request)
    if user_type != 'seller':
        messages.error(request, "Authorization error.")
        return redirect('login')

    order = get_object_or_404(Order, id=order_id, items__product__seller=seller)
    order.status = 'Confirmed'
    order.save()
    messages.success(request, f'Order #{order.id} has been confirmed.')
    return redirect('seller_dashboard')

def delete_order(request, order_id):
    user_type, seller = get_logged_in_user(request)
    if user_type != 'seller':
        messages.error(request, "Authorization error.")
        return redirect('login')

    order = Order.objects.filter(id=order_id, items__product__seller=seller).first()
    if not order:
        messages.error(request, "Order not found or not authorized.")
        return redirect('seller_dashboard')

    order.status = 'Cancelled'
    order.save()
    messages.warning(request, f'Order #{order.id} has been cancelled.')
    return redirect('seller_dashboard')


def delete_feedback(request, feedback_id):
    user_type, seller = get_logged_in_user(request)
    if user_type != 'seller':
        messages.error(request, "Authorization error.")
        return redirect('login')

    feedback = get_object_or_404(Feedback, id=feedback_id, seller=seller)
    feedback.delete()
    messages.info(request, 'Feedback has been deleted.')
    return redirect('seller_dashboard')



# --- Customer Views ---

def customer_dashboard(request):
    products = Product.objects.filter(seller__is_approved=True).order_by('-id')[:12]
    user_type, customer = get_logged_in_user(request)
    
    cart_data = get_cart_context(customer)
    
    context = {
        'products': products,
        'cart_product_ids': cart_data['cart_product_ids'],
        'cart_item_count': cart_data['cart_item_count'],
        'customer': customer,
    }
    return render(request, 'index.html', context)


def products_page(request):
    products_list = Product.objects.filter(seller__is_approved=True).order_by('id')
    user_type, customer = get_logged_in_user(request)
    
    # Search
    query = request.GET.get('q')
    if query:
        products_list = products_list.filter(
            Q(product_name__icontains=query) | Q(description__icontains=query)
        )

   # Category Filter
    category = request.GET.get('category')
    if category:
        products_list = products_list.filter(category__iexact=category)

    # Price Filter
    max_price = request.GET.get('max_price')
    if max_price:
        products_list = products_list.filter(price__lte=max_price)

    # Pagination
    paginator = Paginator(products_list, 30) # Show 30 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    cart_data = get_cart_context(customer)
    
    # Get all distinct categories for the filter sidebar
    categories = Product.objects.filter(seller__is_approved=True).values_list('category', flat=True).distinct()

    context = {
        'products': page_obj, # Pass the paginated page object
        'cart_product_ids': cart_data['cart_product_ids'],
        'cart_item_count': cart_data['cart_item_count'],
        'categories': categories,
    }
    return render(request, 'products.html', context)



def add_to_cart(request, product_id):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Login as customer to add to cart.")
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(customer=customer, product=product)
    if not created:
        messages.info(request, "Already in cart.")
    else:
        messages.success(request, "Added to cart.")
    return redirect(request.META.get('HTTP_REFERER', 'products_page'))


def cart(request):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Login as customer to view cart.")
        return redirect('login')

    cart_items = CartItem.objects.filter(customer=customer)
    subtotal = sum(item.total_price for item in cart_items)
    shipping = Decimal('50.00') if subtotal > 0 else Decimal('0.00')
    total = subtotal + shipping
    
    cart_data = get_cart_context(customer)

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'cart_item_count': cart_data['cart_item_count'],
    }
    return render(request, 'cart.html', context)

def update_cart(request, item_id, action):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Please log in to modify your cart.")
        return redirect('login')

    cart_item = get_object_or_404(CartItem, id=item_id, customer=customer)

    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            # If quantity is 1 and they decrease, remove it
            cart_item.delete()
            messages.info(request, "Item removed from cart.")
    
    return redirect('cart')

def remove_from_cart(request, item_id):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Please log in to modify your cart.")
        return redirect('login')

    cart_item = get_object_or_404(CartItem, id=item_id, customer=customer)
    cart_item.delete()
    messages.success(request, "Item removed from your cart.")
    return redirect('cart')

def checkout(request):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Login to checkout.")
        return redirect('login')

    cart_items = CartItem.objects.filter(customer=customer)
    subtotal = sum(item.total_price for item in cart_items)
    shipping = Decimal('50.00') if subtotal > 0 else Decimal('0.00')
    total = subtotal + shipping
    
    cart_data = get_cart_context(customer)
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'cart_item_count': cart_data['cart_item_count'],
    }
    return render(request, 'checkout.html', context)



@transaction.atomic
def success(request):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Login to complete order.")
        return redirect('login')

    cart_items = CartItem.objects.filter(customer=customer)
    if request.method == 'POST' and cart_items.exists():
        total_price = sum(item.total_price for item in cart_items) + Decimal('50.00')
        
        # Create the Order with address details
        order = Order.objects.create(
            customer=customer, 
            total_price=total_price,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            zip_code=request.POST.get('zip'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
        )
        
        # Create OrderItems and decrease product stock
        for item in cart_items:
            OrderItem.objects.create(
                order=order, 
                product=item.product, 
                quantity=item.quantity, 
                price=item.product.price,
                cost_price=item.product.cost_price  # <-- This line is crucial
            )
            product = item.product
            product.stock -= item.quantity
            product.save()
        
        # Create the Payment record
        Payment.objects.create(
            order=order,
            customer=customer,
            razorpay_payment_id=request.POST.get('razorpay_payment_id'),
            amount=total_price
        )
        
        # Clear the user's cart
        cart_items.delete()
        
    return render(request, 'Success.html')



def about(request):
    user_type, customer = get_logged_in_user(request)
    cart_data = get_cart_context(customer)
    return render(request, 'aboutus.html', {'cart_item_count': cart_data['cart_item_count']})


def community(request):
    user_type, customer = get_logged_in_user(request)
    cart_data = get_cart_context(customer)
    post = CommunityPost.objects.all()
    return render(request, 'community.html', {'cart_item_count': cart_data['cart_item_count'],'post':post})


def my_orders(request):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Login to view orders.")
        return redirect('login')

    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    cart_data = get_cart_context(customer)
    return render(request, 'myorders.html', {'orders': orders, 'cart_item_count': cart_data['cart_item_count']})

def order_detail(request, order_id):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Login to view this order.")
        return redirect('login')

    order = get_object_or_404(Order, id=order_id, customer=customer)
    order_items = OrderItem.objects.filter(order=order)
    try:
        payment = Payment.objects.get(order=order)
    except Payment.DoesNotExist:
        payment = None

    context = {
        'order': order,
        'order_items': order_items,
        'payment': payment,
        'cart_item_count': 0
    }
    return render(request, 'orderdetails.html', context)

def add_feedback(request, order_id, product_id):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer' or request.method != 'POST':
        messages.warning(request, "You must be logged in to leave feedback.")
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    seller = product.seller
    feedback_text = request.POST.get('feedback_text')

    if feedback_text:
        Feedback.objects.create(
            customer=customer,
            seller=seller,
            feedback_text=feedback_text
        )
        messages.success(request, f"Thank you for your feedback on {product.product_name}!")
    else:
        messages.error(request, "Feedback cannot be empty.")
    
    return redirect('order_detail', order_id=order_id)

def profile(request):
    user_type, _ = get_logged_in_user(request)
    if user_type == 'customer':
        return redirect('customer_dashboard')
    elif user_type == 'seller':
        return redirect('seller_dashboard')
    return redirect('login')

def edit_profile(request):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Login to edit your profile.")
        return redirect('login')

    if request.method == 'POST':
        customer.name = request.POST.get('name', customer.name)
        customer.phone = request.POST.get('phone', customer.phone)
        customer.address = request.POST.get('address', customer.address)
        if request.FILES.get('photo'):
            customer.photo = request.FILES.get('photo')
        customer.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('customer_dashboard') # Redirect back to home

    # If it's not a POST request, just redirect back to where they came from
    return redirect(request.META.get('HTTP_REFERER', 'customer_dashboard'))

