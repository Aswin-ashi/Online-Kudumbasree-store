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
    # --- User Facing URLs ---
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/customer/', views.register_customer, name='register_customer'),
    path('register/seller/', views.register_seller, name='register_seller'),
    
    # --- Admin Panel URLs ---
    path('admins/', admin.site.urls),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/customer/delete/<int:customer_id>/', views.delete_customer, name='delete_customer'),
    path('admin/seller/delete/<int:seller_id>/', views.delete_seller, name='delete_seller'),
    path('admin/seller/approve/<int:seller_id>/', views.approve_seller, name='approve_seller'),
    path('admin/seller/reject/<int:seller_id>/', views.reject_seller, name='reject_seller'),
    #--- Seller Panel URLs ---
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/product/add/', views.add_product, name='add_product'),
    path('seller/product/update/<int:product_id>/', views.update_product, name='update_product'),
    path('seller/product/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('seller/order/confirm/<int:order_id>/', views.confirm_order, name='confirm_order'),
    path('seller/order/delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('seller/feedback/delete/<int:feedback_id>/', views.delete_feedback, name='delete_feedback'),
    #--- Seller Panel URLs ---
    path('Home', views.customer_dashboard, name='customer_dashboard'),

    # You would also have paths for your customer_dashboard and seller_dashboard here
    # For example:
    # path('dashboard/customer/', views.customer_dashboard_view, name='customer_dashboard'),
    # path('dashboard/seller/', views.seller_dashboard_view, name='seller_dashboard'),
]

# This is important for serving media files (like user photos) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

