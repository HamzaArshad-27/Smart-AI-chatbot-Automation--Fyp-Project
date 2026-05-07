# 🛍️ Vendora - Premium Multi-Vendor E-Commerce Platform

![Vendora Banner](https://img.shields.io/badge/Vendora-v1.0-5b5fe3?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-4.x-092e20?style=flat-square&logo=django)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169e1?style=flat-square&logo=postgresql)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952b3?style=flat-square&logo=bootstrap)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A modern, full-featured multi-vendor e-commerce marketplace built with Django. Vendora connects buyers with trusted sellers worldwide, featuring a premium dashboard, real-time order tracking, and comprehensive admin management.

---

## 📸 Screenshots

| Landing Page | Admin Dashboard | Company Dashboard |
|:---:|:---:|:---:|
| ![Home](screenshots/home.png) | ![Admin](screenshots/admin.png) | ![Company](screenshots/company.png) |

---

## ✨ Features

### 🏪 Marketplace
- 🔍 **Advanced Product Search** with category filtering
- ⭐ **Product Ratings & Reviews** system
- 🏷️ **Featured Products**, New Arrivals, Best Sellers sections
- 📱 **Fully Responsive** - works on all devices
- 🎨 **Modern Premium UI** with smooth animations

### 👥 User Roles
| Role | Description |
|------|-------------|
| **Admin** | Full platform control, user management, analytics |
| **Company** | Product management, seller management, order processing |
| **Seller** | Product listing, order fulfillment |
| **Retailer** | Bulk purchasing, wholesale pricing |
| **Customer** | Browse products, place orders, write reviews |

### 🔐 Authentication
- ✅ Email-based registration with OTP verification
- 🔑 Secure login with remember-me functionality
- 🔄 Password reset via email OTP
- ⏳ Admin approval workflow for new accounts
- 👤 Profile management with avatar upload

### 📊 Admin Dashboard
- 📈 Real-time analytics & revenue charts
- 👥 Complete User CRUD management
- ✅ Pending user approval system
- 🗂️ Category management (CRUD)
- 📋 Bulk user actions (approve, delete, deactivate)
- 🔍 Advanced user search & filtering

### 🛒 Shopping Features
- 🛍️ Add to cart (AJAX)
- 📦 Order management
- 💳 Multiple payment methods
- 📧 Email notifications
- 🏷️ Discount & promo support

### 🏢 Company Dashboard
- 📊 Sales analytics & reports
- 👨‍💼 Seller management
- 📦 Product inventory management
- 📋 Order processing & tracking
- ⚠️ Low stock alerts

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|:-----------|:-------:|:--------|
| **Django** | 4.x | Web framework |
| **PostgreSQL** | 15 | Primary database |
| **Celery** | 5.x | Async tasks & email |
| **Redis** | 7.x | Message broker & caching |
| **Django Crispy Forms** | 2.x | Form rendering |
| **Django Filter** | 23.x | Advanced filtering |
| **Pillow** | 10.x | Image processing |
| **python-decouple** | 3.x | Environment variables |

### Frontend
| Technology | Purpose |
|:-----------|:--------|
| **Bootstrap 5** | UI framework |
| **Chart.js** | Analytics charts |
| **AOS** | Scroll animations |
| **Font Awesome 6** | Icons |
| **Google Fonts** | Typography (Inter, Plus Jakarta Sans) |

### DevOps
| Technology | Purpose |
|:-----------|:--------|
| **WhiteNoise** | Static files serving |
| **django-cors-headers** | CORS handling |
| **Gunicorn** | WSGI server (production) |

---

## 📁 Project Structure
vendora/
│
├── apps/
│ ├── accounts/ # User authentication & profiles
│ │ ├── models.py # User & OTP models
│ │ ├── views.py # Auth views (register, login, OTP, password reset)
│ │ ├── forms.py # Registration, login, profile forms
│ │ └── urls.py # Auth URL patterns
│ │
│ ├── companies/ # Company & seller management
│ │ ├── models.py # Company, Seller models
│ │ ├── views.py # Company dashboard views
│ │ └── urls.py # Company URL patterns
│ │
│ ├── products/ # Product & category management
│ │ ├── models.py # Product, Category models
│ │ ├── views.py # Product CRUD, API endpoints
│ │ └── urls.py # Product URL patterns
│ │
│ ├── orders/ # Order processing
│ │ ├── models.py # Order, OrderItem models
│ │ ├── views.py # Order management views
│ │ └── urls.py # Order URL patterns
│ │
│ ├── cart/ # Shopping cart
│ │ ├── models.py # Cart, CartItem models
│ │ ├── views.py # Cart AJAX views
│ │ └── urls.py # Cart URL patterns
│ │
│ ├── reports/ # Analytics & reports
│ │ └── views.py # Report generation views
│ │
│ └── core/ # Core app (home, about, contact)
│ ├── views.py # Home page, static pages
│ ├── urls.py # Core URL patterns
│ └── context_processors.py
│
├── static/ # Static files (CSS, JS, Images)
│ ├── css/
│ │ └── dashboard/
│ │ └── dashboard.css
│ └── js/
│ └── dashboard/
│ └── dashboard.js
│
├── templates/ # HTML templates
│ ├── base.html # Base template
│ ├── dashboard/
│ │ ├── base_dashboard.html
│ │ ├── admin.html
│ │ ├── company.html
│ │ ├── all_users.html
│ │ ├── pending_users.html
│ │ └── ...
│ ├── accounts/
│ │ ├── login.html
│ │ ├── register.html
│ │ ├── verify_otp.html
│ │ ├── pending_approval.html
│ │ ├── forgot_password.html
│ │ └── reset_password.html
│ └── core/
│ ├── home.html
│ └── includes/
│ └── product_grid.html
│
├── media/ # User uploaded files
├── staticfiles/ # Collected static files
├── vendora/ # Project configuration
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
│
├── .env # Environment variables
├── .env.example # Environment variables template
├── .gitignore
├── manage.py
├── requirements.txt # Python dependencies
└── README.md


---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **PostgreSQL 15+**
- **Redis** (for Celery)
- **Git**

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/vendora.git
cd vendora
