import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
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
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # --- Admin Login ---
        if username == 'admin' and password == 'adminpass':
            request.session['user_type'] = 'admin'
            request.session['user_id'] = 0
            request.session.modified = True
            messages.success(request, 'Welcome Admin!')
            if next_url:
                return redirect(next_url)
            return redirect('admin_dashboard')

        # --- Customer Login ---
        try:
            customer = Customer.objects.get(username=username)
            if password == customer.password:
                request.session['user_type'] = 'customer'
                request.session['user_id'] = customer.id
                messages.success(request, f'Welcome {customer.name}!')
                if next_url:
                    return redirect(next_url)
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
                if next_url:
                    return redirect(next_url)
                return redirect('seller_dashboard')
        except Seller.DoesNotExist:
            pass

        messages.error(request, 'Invalid credentials or seller not approved.')
        return render(request, 'login.html', {'next': next_url})

    return render(request, 'login.html', {'next': next_url})




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
    orders = Order.objects.all().order_by('-created_at')
    
    context = {
        'customers': customers,
        'approved_sellers': approved_sellers,
        'pending_sellers': pending_sellers,
        'posts': posts,
        'orders': orders,
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

    # --- Sales Report Logic ---
    current_time = timezone.now()
    selected_year = int(request.GET.get('year', current_time.year))
    selected_month = int(request.GET.get('month', current_time.month))

    items_sold = OrderItem.objects.filter(
        product__seller=seller,
        order__created_at__year=selected_year,
        order__created_at__month=selected_month
    )

    total_sales = items_sold.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
    total_cost = items_sold.aggregate(total=Sum(F('cost_price') * F('quantity')))['total'] or 0
    total_profit = total_sales - total_cost
    total_products_sold = items_sold.aggregate(total=Sum('quantity'))['total'] or 0

    product_sales = items_sold.values('product__product_name').annotate(
        total_quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price')),
        total_cost=Sum(F('quantity') * F('cost_price'))
    ).annotate(
        total_profit=ExpressionWrapper(F('total_revenue') - F('total_cost'), output_field=DecimalField())
    ).order_by('-total_profit')

    years = range(2024, current_time.year + 1)
    months = [
        {"value": 1, "name": "January"}, {"value": 2, "name": "February"},
        {"value": 3, "name": "March"}, {"value": 4, "name": "April"},
        {"value": 5, "name": "May"}, {"value": 6, "name": "June"},
        {"value": 7, "name": "July"}, {"value": 8, "name": "August"},
        {"value": 9, "name": "September"}, {"value": 10, "name": "October"},
        {"value": 11, "name": "November"}, {"value": 12, "name": "December"}
    ]

    products = Product.objects.filter(seller=seller)
    orders = Order.objects.filter(items__product__seller=seller).distinct().order_by('-created_at')
    feedbacks = Feedback.objects.filter(seller=seller).order_by('-created_at')

    context = {
        'seller': seller,
        'products': products,
        'orders': orders,
        'feedbacks': feedbacks,
        'total_sales': total_sales,
        'total_profit': total_profit,
        'total_products_sold': total_products_sold,
        'product_sales': product_sales,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'years': years,
        'months': months,
    }
    return render(request, 'seller_dashboard.html', context)


def add_product(request):
    user_type, seller = get_logged_in_user(request)
    if user_type != 'seller' or request.method != 'POST':
        messages.warning(request, "Action requires seller login.")
        return redirect('seller_dashboard')

    try:
        price_val = Decimal(request.POST.get('price', '0'))
        cost_price_val = Decimal(request.POST.get('cost_price', '0') or '0')
        stock_val = int(request.POST.get('stock', '0'))
    except (ValueError, Exception):
        messages.error(request, "Invalid numeric input for price or stock.")
        return redirect('seller_dashboard')

    Product.objects.create(
        seller=seller,
        product_name=request.POST.get('product_name', '').strip(),
        price=price_val,
        cost_price=cost_price_val,
        stock=stock_val,
        description=request.POST.get('description', '').strip(),
        category=request.POST.get('category', 'General').strip(),
        photo=request.FILES.get('photo')
    )
    messages.success(request, "Product added successfully!")
    return redirect('seller_dashboard')


def update_product(request, product_id):
    user_type, seller = get_logged_in_user(request)
    product = get_object_or_404(Product, id=product_id)
    if product.seller != seller or request.method != 'POST':
        messages.warning(request, "Not authorized.")
        return redirect('seller_dashboard')

    try:
        if request.POST.get('price'):
            product.price = Decimal(request.POST.get('price'))
        if request.POST.get('cost_price'):
            product.cost_price = Decimal(request.POST.get('cost_price'))
        if request.POST.get('stock'):
            product.stock = int(request.POST.get('stock'))
    except (ValueError, Exception):
        messages.error(request, "Invalid numeric input for price or stock.")
        return redirect('seller_dashboard')

    product.product_name = request.POST.get('product_name', product.product_name)
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
    order.status = 'Order Packed Confirmed by Seller'
    order.save()
    messages.success(request, f'Order #{order.id} has been packed & confirmed.')
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
        'customer': customer,
    }
    return render(request, 'products.html', context)



def add_to_cart(request, product_id):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Login as customer to add to cart.")
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    if product.stock <= 0:
        messages.error(request, f"Sorry, '{product.product_name}' is currently out of stock.")
        return redirect(request.META.get('HTTP_REFERER', None) or 'products')

    cart_item, created = CartItem.objects.get_or_create(customer=customer, product=product)
    if not created:
        if cart_item.quantity + 1 > product.stock:
            messages.warning(request, f"Cannot add more. Maximum available stock is {product.stock}.")
        else:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Updated quantity for {product.product_name}.")
    else:
        messages.success(request, f"Added {product.product_name} to cart.")
    return redirect(request.META.get('HTTP_REFERER', None) or 'products')


FREE_DELIVERY_THRESHOLD = Decimal('500.00')
DEFAULT_SHIPPING = Decimal('50.00')

def cart(request):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Login as customer to view cart.")
        return redirect('login')

    cart_items = CartItem.objects.filter(customer=customer)
    subtotal = sum(item.total_price for item in cart_items)
    
    if subtotal >= FREE_DELIVERY_THRESHOLD or subtotal == Decimal('0.00'):
        shipping = Decimal('0.00')
        is_free_delivery = True
        amount_needed_for_free_delivery = Decimal('0.00')
    else:
        shipping = DEFAULT_SHIPPING
        is_free_delivery = False
        amount_needed_for_free_delivery = FREE_DELIVERY_THRESHOLD - subtotal

    total = subtotal + shipping
    cart_data = get_cart_context(customer)

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'is_free_delivery': is_free_delivery,
        'amount_needed_for_free_delivery': amount_needed_for_free_delivery,
        'free_delivery_threshold': FREE_DELIVERY_THRESHOLD,
        'cart_item_count': cart_data['cart_item_count'],
        'customer': customer,
    }
    return render(request, 'cart.html', context)

def update_cart(request, item_id, action):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer':
        messages.warning(request, "Please log in to modify your cart.")
        return redirect('login')

    cart_item = get_object_or_404(CartItem, id=item_id, customer=customer)

    if action == 'increase':
        if cart_item.quantity + 1 > cart_item.product.stock:
            messages.warning(request, f"Cannot add more. Stock limit is {cart_item.product.stock} units.")
        else:
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
    
    if subtotal >= FREE_DELIVERY_THRESHOLD or subtotal == Decimal('0.00'):
        shipping = Decimal('0.00')
        is_free_delivery = True
    else:
        shipping = DEFAULT_SHIPPING
        is_free_delivery = False

    total = subtotal + shipping
    cart_data = get_cart_context(customer)
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'is_free_delivery': is_free_delivery,
        'cart_item_count': cart_data['cart_item_count'],
        'customer': customer,
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
        subtotal = sum(item.total_price for item in cart_items)
        shipping = Decimal('0.00') if subtotal >= FREE_DELIVERY_THRESHOLD else DEFAULT_SHIPPING
        total_price = subtotal + shipping
        
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
    return render(request, 'aboutus.html', {'cart_item_count': cart_data['cart_item_count'], 'customer': customer})


def community(request):
    user_type, customer = get_logged_in_user(request)
    cart_data = get_cart_context(customer)
    post = CommunityPost.objects.all().order_by('-created_at')
    inspired_posts = request.session.get('inspired_posts', [])
    return render(request, 'community.html', {
        'cart_item_count': cart_data['cart_item_count'], 
        'post': post, 
        'customer': customer,
        'inspired_posts': inspired_posts
    })


def toggle_inspired(request, post_id):
    post_obj = get_object_or_404(CommunityPost, id=post_id)
    inspired_posts = request.session.get('inspired_posts', [])
    
    if post_id in inspired_posts:
        inspired_posts.remove(post_id)
        if post_obj.inspired_count > 0:
            post_obj.inspired_count -= 1
        is_inspired = False
    else:
        inspired_posts.append(post_id)
        post_obj.inspired_count += 1
        is_inspired = True

    post_obj.save()
    request.session['inspired_posts'] = inspired_posts
    request.session.modified = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({'inspired_count': post_obj.inspired_count, 'is_inspired': is_inspired})

    return redirect('community')


def my_orders(request):
    user_type, customer = get_logged_in_user(request)
    if user_type == 'seller':
        return redirect('seller_dashboard')
    elif user_type == 'admin':
        return redirect('admin_dashboard')
    elif user_type != 'customer':
        messages.warning(request, "Please log in to view your orders.")
        return redirect(f"/login/?next={request.path}")

    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    cart_data = get_cart_context(customer)
    return render(request, 'myorders.html', {'orders': orders, 'cart_item_count': cart_data['cart_item_count'], 'customer': customer})


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

    cart_data = get_cart_context(customer)
    context = {
        'order': order,
        'order_items': order_items,
        'payment': payment,
        'cart_item_count': cart_data['cart_item_count'],
        'customer': customer,
    }
    return render(request, 'orderdetails.html', context)

def add_feedback(request, order_id, product_id):
    user_type, customer = get_logged_in_user(request)
    if user_type != 'customer' or request.method != 'POST':
        messages.warning(request, "You must be logged in to leave feedback.")
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    seller = product.seller
    feedback_text = request.POST.get('feedback_text', '').strip()
    try:
        rating_val = int(request.POST.get('rating', 5))
    except ValueError:
        rating_val = 5

    Feedback.objects.update_or_create(
        customer=customer,
        product=product,
        defaults={
            'seller': seller,
            'feedback_text': feedback_text if feedback_text else f"Rated {rating_val} stars by {customer.name}",
            'rating': rating_val
        }
    )
    
    # Recalculate product-specific average rating
    from django.db.models import Avg
    avg_rating = Feedback.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg']
    if avg_rating is not None:
        product.rating = Decimal(str(round(avg_rating, 1)))
        product.save()

    messages.success(request, f"Thank you! Your {rating_val}-star rating for {product.product_name} has been recorded.")
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

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user_type, customer = get_logged_in_user(request)
    
    cart_data = get_cart_context(customer)

    seller = product.seller
    feedbacks = Feedback.objects.filter(product=product).select_related('customer').order_by('-id')
    review_count = feedbacks.count()
    
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    if len(related_products) < 4:
        extra_products = Product.objects.exclude(id=product.id).exclude(id__in=related_products.values_list('id', flat=True))[:4 - len(related_products)]
        related_products = list(related_products) + list(extra_products)

    context = {
        'product': product,
        'seller': seller,
        'feedbacks': feedbacks,
        'review_count': review_count,
        'cart_product_ids': cart_data['cart_product_ids'],
        'cart_item_count': cart_data['cart_item_count'],
        'related_products': related_products,
        'user_type': user_type,
        'customer': customer,
    }
    return render(request, 'product_detail.html', context)


def community(request):
    user_type, customer = get_logged_in_user(request)
    posts = CommunityPost.objects.all().order_by('-created_at')
    
    inspired_posts = request.session.get('inspired_posts', [])
    cart_data = get_cart_context(customer)

    context = {
        'post': posts,
        'inspired_posts': inspired_posts,
        'cart_product_ids': cart_data['cart_product_ids'],
        'cart_item_count': cart_data['cart_item_count'],
        'customer': customer,
    }
    return render(request, 'community.html', context)


def toggle_inspired(request, post_id):
    post_obj = get_object_or_404(CommunityPost, id=post_id)
    inspired_posts = request.session.get('inspired_posts', [])
    
    if post_id in inspired_posts:
        inspired_posts.remove(post_id)
        if post_obj.inspired_count > 0:
            post_obj.inspired_count -= 1
            post_obj.save()
        is_inspired = False
    else:
        inspired_posts.append(post_id)
        post_obj.inspired_count += 1
        post_obj.save()
        is_inspired = True

    request.session['inspired_posts'] = inspired_posts
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'inspired_count': post_obj.inspired_count,
        'is_inspired': is_inspired
    })

