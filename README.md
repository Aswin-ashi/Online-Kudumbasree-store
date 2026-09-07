# 🛒 Online Kudumbashree Store

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-092E20.svg?style=flat-square&logo=django)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Web-purple.svg?style=flat-square)]()

A modern, community-driven e-commerce platform designed to empower **Kudumbashree Neighborhood Groups (NHGs)** in Kerala by bringing authentic, handcrafted, and organic products directly to consumers worldwide.

---

## 📌 Overview

The **Online Kudumbashree Store** is a full-featured e-commerce ecosystem built with **Django** and modern web technologies. It connects verified micro-enterprises and women entrepreneurs in Kerala directly with buyers, fostering local economic growth while providing consumers with verified, direct-from-source traditional items.

---

## ✨ Key Features

### 🛍️ Customer Experience
- **Interactive Product Catalog**: Browse organic produce, ethnic foods, handicrafts, and daily essentials with category filtering.
- **Dynamic Star Ratings**: Dynamic 5-star rating calculation based on real customer feedback and reviews.
- **Shopping Cart & Checkout**: Intuitive cart management with real-time price totals.
- **Secure Payment Integration**: Seamless checkout powered by **Razorpay** payment gateway.
- **Order Tracking & History**: Customers can view past orders, current delivery statuses, and itemized breakdown.
- **Product & Seller Reviews**: Leave feedback and star ratings for items purchased.

### 👩‍🌾 Seller / NHG Unit Member Portal
- **Seller Registration & Verification**: Onboarding for Kudumbashree unit members with NHG details and passbook document upload.
- **Admin Approval Workflow**: Verification system ensuring only authorized NHG members list products.
- **Seller Dashboard**: Manage inventory, track product stock, monitor cost prices, and calculate net profits.
- **Product Management**: Add, update, and manage product listings with custom images or automated high-quality fallbacks.

### 🛡️ Admin & Community Hub
- **Seller Verification**: Review and approve pending NHG seller applications.
- **Community Wall / Inspiration**: Create community posts highlighting seller stories with interactive "Inspired" counters.
- **Platform Analytics**: Comprehensive view of users, active orders, and sales activity.

---

## 🛠️ Tech Stack

- **Backend**: Python, Django 5.x
- **Frontend**: HTML5, Vanilla CSS, Glassmorphism UI components, JavaScript
- **Database**: SQLite (Development) / PostgreSQL compatible
- **Payments**: Razorpay Payment API
- **Media & Assets**: Custom file uploads with Unsplash fallback integration

---

## 📁 Repository Structure

```
store/
├── manage.py                # Django management script
├── db.sqlite3               # Development database
├── requirements.txt         # Project dependencies
├── README.md                # Project documentation
├── LICENSE                  # License details
├── store/                   # Project configuration directory
│   ├── settings.py          # App settings & database config
│   ├── urls.py              # Root URL routing
│   ├── wsgi.py              # WSGI server entry point
│   └── asgi.py              # ASGI server entry point
├── storeapp/                # Main application logic
│   ├── models.py            # Customer, Seller, Product, Order, Feedback models
│   ├── views.py             # View functions and business logic
│   ├── admin.py             # Django Admin customization
│   └── urls.py              # App-specific URL routes
├── templates/               # HTML Templates
│   ├── index.html           # Main landing page
│   ├── products.html        # Product listing & details
│   ├── cart.html            # Shopping cart
│   ├── checkout.html        # Checkout & Razorpay payment
│   ├── seller_dashboard.html# Seller management dashboard
│   ├── seller_reg.html      # NHG member registration
│   └── myorders.html        # Customer order tracking
└── static/                  # CSS, JS, and image assets
```

---

## 🚀 Quick Start & Local Setup

### Prerequisites
- **Python 3.10+** installed on your system
- **Git** installed

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Aswin-ashi/Demo-Online-Kudumbasree-store-.git
   cd Demo-Online-Kudumbasree-store-/store
   ```

2. **Create & Activate a Virtual Environment**
   ```bash
   # On Windows
   python -m venv djangoenv
   djangoenv\Scripts\activate

   # On macOS/Linux
   python3 -m venv djangoenv
   source djangoenv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install django razorpay pillow
   ```

4. **Apply Database Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create Superuser (Admin)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run Development Server**
   ```bash
   python manage.py runserver
   ```
   Open your browser and navigate to `http://127.0.0.1:8000/`.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Aswin-ashi/Demo-Online-Kudumbasree-store-/issues).
