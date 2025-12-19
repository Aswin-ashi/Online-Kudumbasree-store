"""
URL configuration for store project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from storeapp import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.login_view, name='login'), # Set login as the root
    path('logout/', views.logout_view, name='logout'),
    path('register/customer/', views.register_customer, name='register_customer'),
    path('register/seller/', views.register_seller, name='register_seller'),
    
    # --- Main Site Pages (Customer Facing) ---
     path('home/', views.customer_dashboard, name='customer_dashboard'),
    path('products/', views.products_page, name='products'),
    path('about/', views.about, name='about'),
    path('community/', views.community, name='community'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('success/', views.success, name='success'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('my_orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/feedback/<int:product_id>/', views.add_feedback, name='add_feedback'),

    # --- Admin Panel URLs ---
    path('admins/', admin.site.urls),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/customer/delete/<int:customer_id>/', views.delete_customer, name='delete_customer'),
    path('admin/seller/delete/<int:seller_id>/', views.delete_seller, name='delete_seller'),
    path('admin/seller/approve/<int:seller_id>/', views.approve_seller, name='approve_seller'),
    path('admin/seller/reject/<int:seller_id>/', views.reject_seller, name='reject_seller'),
    path('admin/post/add/', views.add_post, name='add_post'),
    path('admin/post/update/<int:post_id>/', views.update_post, name='update_post'),
    path('admin/post/delete/<int:post_id>/', views.delete_post, name='delete_post'),


    #--- Seller Panel URLs ---
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/product/add/', views.add_product, name='add_product'),
    path('seller/product/update/<int:product_id>/', views.update_product, name='update_product'),
    path('seller/product/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('seller/order/confirm/<int:order_id>/', views.confirm_order, name='confirm_order'),
    path('seller/order/delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('seller/feedback/delete/<int:feedback_id>/', views.delete_feedback, name='delete_feedback'),


]

# This is important for serving media files (like user photos) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

