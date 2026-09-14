# Vendora — Premium Multi-Vendor E-Commerce Platform

![Vendora Banner](https://img.shields.io/badge/Vendora-v1.0-5b5fe3?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-5.x-092e20?style=flat-square\&logo=django)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=flat-square\&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-4169e1?style=flat-square\&logo=postgresql)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952b3?style=flat-square\&logo=bootstrap)
![Redis](https://img.shields.io/badge/Redis-7%2B-dc382d?style=flat-square\&logo=redis)
![Celery](https://img.shields.io/badge/Celery-5.x-37814a?style=flat-square\&logo=celery)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Vendora** is a modern, full-featured **multi-vendor e-commerce marketplace** built with Django.

The platform allows multiple companies and sellers to manage products, inventory, orders, customers, and sales while customers can browse products, add items to their cart, place orders, submit reviews, and track purchases.

Vendora also includes dashboards, analytics, role-based access control, email/OTP authentication, background task processing, and an AI-powered product assistant.

---

# 📸 Screenshots

|          Landing Page         |         Admin Dashboard         |          Company Dashboard          |
| :---------------------------: | :-----------------------------: | :---------------------------------: |
| ![Home](screenshots/home.png) | ![Admin](screenshots/admin.png) | ![Company](screenshots/company.png) |

> Add your screenshots inside the `screenshots/` directory.

Example:

```text
screenshots/
├── home.png
├── admin.png
├── company.png
├── products.png
├── product-detail.png
└── orders.png
```

---

# ✨ Features

## 🏪 Marketplace

* 🔍 Advanced product search
* 🗂️ Category-based filtering
* ⭐ Product ratings and reviews
* 🏷️ Featured products
* 🆕 New arrivals
* 🔥 Best-selling products
* 📱 Fully responsive design
* 🎨 Modern premium UI
* 🛒 AJAX-powered shopping cart
* 📦 Complete order management
* 💳 Multiple payment methods
* 🏷️ Discounts and promotional support
* 📧 Email notifications

---

# 👥 User Roles

Vendora supports multiple user roles with different permissions.

| Role             | Description                                                                     |
| ---------------- | ------------------------------------------------------------------------------- |
| 👑 **Admin**     | Complete platform control, user management, analytics, categories and approvals |
| 🏢 **Company**   | Manages products, sellers, inventory and company orders                         |
| 👨‍💼 **Seller** | Lists products and fulfills assigned orders                                     |
| 🏬 **Retailer**  | Supports bulk/wholesale purchasing                                              |
| 🛍️ **Customer** | Browses products, purchases items and submits reviews                           |

### Role-Based Access

Each user type has access only to the features and data relevant to their role.

For example:

```text
Admin
   │
   ├── Users
   ├── Companies
   ├── Categories
   ├── Products
   ├── Orders
   └── Reports

Company
   │
   ├── Sellers
   ├── Products
   ├── Inventory
   ├── Orders
   └── Reports

Seller
   │
   ├── Products
   └── Orders

Customer
   │
   ├── Products
   ├── Cart
   ├── Orders
   └── Reviews
```

---

# 🔐 Authentication & Security

Vendora provides a complete authentication workflow.

### Authentication Features

* 📧 Email-based registration
* 🔢 OTP verification
* 🔑 Secure login
* ☑️ Remember-me functionality
* 🔄 Password reset
* 📩 Password reset through email OTP
* ⏳ Admin approval workflow
* 👤 Profile management
* 🖼️ Avatar/profile image upload
* 🔒 Role-based authorization
* 🛡️ Django CSRF protection
* 🔐 Environment-based secrets

---

# 📊 Admin Dashboard

The Admin Dashboard provides complete control over the marketplace.

### Dashboard Features

* 📈 Sales analytics
* 💰 Revenue statistics
* 📦 Order statistics
* 👥 User statistics
* 📊 Charts and reports
* 👤 User CRUD
* ✅ Pending user approvals
* 🗂️ Category management
* 🔍 User search
* 🎯 User filtering
* ⚡ Bulk user actions
* 🚫 Account deactivation
* 🗑️ User deletion

---

# 🏢 Company Dashboard

Companies have their own management dashboard.

### Company Features

* 📊 Sales analytics
* 📦 Product management
* 👨‍💼 Seller management
* 📋 Order processing
* 📦 Inventory management
* ⚠️ Low-stock monitoring
* 📈 Sales reports
* 👥 Seller assignment

---

# 🤖 AI Product Assistant

Vendora includes an AI-powered assistant designed to help customers interact naturally with the marketplace.

The assistant can be used for:

* 🔎 Product discovery
* 🛍️ Product recommendations
* 🗂️ Category-related questions
* 💰 Product price queries
* 📦 Product information
* 🧠 Semantic product search
* 💬 Natural-language conversations

### AI Architecture

```text
Customer
    │
    ▼
Vendora AI Chat
    │
    ▼
Django AI Backend
    │
    ├── Product Data
    │
    ├── Category Data
    │
    ├── Semantic Search
    │
    └── AI Model
            │
            ▼
        Ollama / LLM
```

The AI system can use local language models through **Ollama**, helping keep AI processing local during development.

---

# 🧠 Semantic Search & Embeddings

Vendora can use vector embeddings for semantic product search.

The general workflow is:

```text
Products
   │
   ▼
Text Representation
   │
   ▼
Embedding Model
   │
   ▼
Vector Database / FAISS
   │
   ▼
Semantic Search
   │
   ▼
Relevant Products
```

This allows users to search using natural language instead of only exact product names.

For example:

```text
"I need something for home workouts"
```

can find products related to:

```text
Dumbbells
Pull-up Bars
Exercise Equipment
Yoga Mats
Resistance Bands
```

---

# 🛠️ Technology Stack

## Backend

| Technology              | Purpose                    |
| ----------------------- | -------------------------- |
| **Python**              | Programming language       |
| **Django**              | Web framework              |
| **PostgreSQL**          | Relational database        |
| **Celery**              | Background task processing |
| **Redis**               | Message broker/cache       |
| **Django Crispy Forms** | Form rendering             |
| **Django Filter**       | Filtering                  |
| **Pillow**              | Image processing           |
| **python-decouple**     | Environment configuration  |
| **django-cors-headers** | CORS handling              |

## Frontend

| Technology       | Purpose                   |
| ---------------- | ------------------------- |
| **HTML5**        | Page structure            |
| **CSS3**         | Styling                   |
| **Bootstrap 5**  | Responsive UI             |
| **JavaScript**   | Client-side functionality |
| **AJAX**         | Asynchronous requests     |
| **Chart.js**     | Analytics charts          |
| **AOS**          | Scroll animations         |
| **Font Awesome** | Icons                     |
| **Google Fonts** | Typography                |

## AI

| Technology                | Purpose                   |
| ------------------------- | ------------------------- |
| **Ollama**                | Local LLM runtime         |
| **LangChain**             | AI integration            |
| **LangGraph**             | AI workflow orchestration |
| **FAISS**                 | Vector similarity search  |
| **Sentence Transformers** | Text embeddings           |

## Production / DevOps

| Technology     | Purpose                |
| -------------- | ---------------------- |
| **Gunicorn**   | Production WSGI server |
| **WhiteNoise** | Static file serving    |
| **Git**        | Version control        |
| **GitHub**     | Source code hosting    |

---

# 📁 Project Structure

```text
vendora/
│
├── apps/
│   │
│   ├── accounts/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── ...
│   │
│   ├── companies/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── ...
│   │
│   ├── products/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── ...
│   │
│   ├── cart/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── ...
│   │
│   ├── orders/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── ...
│   │
│   ├── reports/
│   │   ├── views.py
│   │   └── ...
│   │
│   ├── ai_assistant/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── ai_response.py
│   │   ├── ...
│   │   └── management/
│   │
│   └── core/
│       ├── views.py
│       ├── urls.py
│       ├── context_processors.py
│       └── ...
│
├── templates/
│   ├── base.html
│   │
│   ├── accounts/
│   ├── companies/
│   ├── products/
│   ├── cart/
│   ├── orders/
│   ├── dashboard/
│   ├── ai/
│   └── core/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/
│
├── staticfiles/
│
├── vendora/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── ...
│
├── manage.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

# 🚀 Installation

## 1. Prerequisites

Make sure the following software is installed.

* Python 3.10+
* PostgreSQL 15+
* Redis 7+
* Git
* Ollama (optional, for AI features)

Check Python:

```powershell
python --version
```

Check Git:

```powershell
git --version
```

Check PostgreSQL:

```powershell
psql --version
```

Check Redis:

```powershell
redis-cli --version
```

---

# 📥 2. Clone the Repository

```powershell
git clone https://github.com/yourusername/vendora.git
```

Move into the project:

```powershell
cd vendora
```

---

# 🐍 3. Create a Virtual Environment

Create a virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then:

```powershell
.\venv\Scripts\Activate.ps1
```

You should see:

```text
(venv) PS C:\...\vendora>
```

---

# 📦 4. Install Dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install project dependencies:

```powershell
pip install -r requirements.txt
```

---

# 🗄️ 5. PostgreSQL Database Setup

Create a PostgreSQL database.

Open PostgreSQL:

```powershell
psql -U postgres
```

Create the database:

```sql
CREATE DATABASE vendora;
```

Create a database user if required:

```sql
CREATE USER vendora_user WITH PASSWORD 'your_password';
```

Grant permissions:

```sql
GRANT ALL PRIVILEGES ON DATABASE vendora TO vendora_user;
```

Exit PostgreSQL:

```sql
\q
```

---

# ⚙️ 6. Environment Variables

Create a `.env` file in the project root.

Example:

```env
DEBUG=True

SECRET_KEY=your-secret-key

ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=vendora
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=127.0.0.1
DB_PORT=5432

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_email_app_password

REDIS_URL=redis://127.0.0.1:6379/0

OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

> Never commit your real `.env` file to GitHub.

Use `.env.example` to document the required variables.

---

# 🔄 7. Apply Database Migrations

Run:

```powershell
python manage.py makemigrations
```

Then:

```powershell
python manage.py migrate
```

Check migration status:

```powershell
python manage.py showmigrations
```

---

# 👑 8. Create Admin/Superuser

Create a Django superuser:

```powershell
python manage.py createsuperuser
```

Follow the prompts:

```text
Username:
Email:
Password:
Password (again):
```

---

# 🖼️ 9. Collect Static Files

For production/static deployment:

```powershell
python manage.py collectstatic
```

If prompted:

```text
Type 'yes' to continue
```

---

# 🧪 10. Check the Project

Run Django's system checks:

```powershell
python manage.py check
```

For deployment-related checks:

```powershell
python manage.py check --deploy
```

---

# ▶️ 11. Start the Development Server

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

---

# 🔴 Redis Setup

Redis is required for background tasks and Celery workflows.

Check whether Redis is running:

```powershell
redis-cli ping
```

Expected result:

```text
PONG
```

If Redis is installed as a Windows service, start it using your configured service.

If using WSL/Docker, start Redis through that environment.

---

# 🌿 Celery Setup

Celery handles asynchronous/background tasks.

Start the Celery worker from the project directory.

### Windows

```powershell
celery -A vendora worker --loglevel=info --pool=solo
```

If your Celery application is configured differently, use the corresponding application module.

Keep the Celery worker running in a separate terminal.

Example:

```text
Terminal 1
---------
python manage.py runserver

Terminal 2
---------
celery -A vendora worker --loglevel=info --pool=solo

Terminal 3
---------
redis-server
```

---

# 🤖 Ollama AI Setup

The AI assistant requires Ollama if you want to run the local AI functionality.

Install Ollama from the official Ollama website.

After installation, verify it:

```powershell
ollama --version
```

Check installed models:

```powershell
ollama list
```

Pull the recommended model:

```powershell
ollama pull qwen2.5:3b
```

Verify:

```powershell
ollama list
```

Run the model manually if required:

```powershell
ollama run qwen2.5:3b
```

Ollama normally runs on:

```text
http://127.0.0.1:11434
```

---

# 🧠 Rebuild Product Embeddings

If Vendora's AI assistant uses semantic product search, embeddings may need to be rebuilt after adding or changing products.

Example:

```powershell
python manage.py rebuild_embeddings
```

For a limited number of products:

```powershell
python manage.py rebuild_embeddings --limit 100
```

After changing a large number of products, rebuild the embeddings again.

---

# 🔍 Verify AI Configuration

Make sure your `.env` contains the required AI configuration.

Example:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

Then start Django:

```powershell
python manage.py runserver
```

The AI endpoint can then be accessed through the application's configured AI URL.

---

# 📧 Email Configuration

Vendora can use email for:

* Account verification
* OTP verification
* Password reset
* Notifications
* Order-related emails

For Gmail, use an **App Password** rather than your normal Gmail password.

Example:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

Never publish email credentials in GitHub.

---

# 🛒 Typical User Flow

```text
Customer
   │
   ▼
Register
   │
   ▼
Email OTP Verification
   │
   ▼
Admin Approval
   │
   ▼
Login
   │
   ▼
Browse Products
   │
   ▼
Search / Filter
   │
   ▼
Product Details
   │
   ▼
Add to Cart
   │
   ▼
Checkout
   │
   ▼
Place Order
   │
   ▼
Order Tracking
   │
   ▼
Review Product
```

---

# 🏢 Company Workflow

```text
Admin
  │
  ▼
Approve Company
  │
  ▼
Company Dashboard
  │
  ├── Manage Sellers
  │
  ├── Add Products
  │
  ├── Manage Inventory
  │
  ├── Process Orders
  │
  └── View Reports
```

---

# 📦 Order Workflow

A typical order can move through several states:

```text
Pending
   │
   ▼
Confirmed
   │
   ▼
Processing
   │
   ▼
Shipped
   │
   ▼
Delivered
```

Possible cancellation flow:

```text
Pending / Processing
        │
        ▼
    Cancelled
```

> The exact statuses depend on the order models and business rules implemented in the project.

---

# 🔎 Product Search

Customers can search and filter products using:

* Product name
* Category
* Price
* Availability
* Other supported filters

Example:

```text
Search:
"Mountain Bike"
```

The application returns matching products.

With semantic search enabled, users can also search using natural-language descriptions.

---

# 🧪 Development Commands

## Start server

```powershell
python manage.py runserver
```

## Start server on a custom port

```powershell
python manage.py runserver 8080
```

## Run migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

## Check migrations

```powershell
python manage.py showmigrations
```

## Create superuser

```powershell
python manage.py createsuperuser
```

## Django shell

```powershell
python manage.py shell
```

## Run tests

```powershell
python manage.py test
```

## Check project

```powershell
python manage.py check
```

## Collect static files

```powershell
python manage.py collectstatic
```

---

# 🧹 Useful Maintenance Commands

Clear Python cache files manually if necessary:

```powershell
Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

Check installed packages:

```powershell
pip list
```

Save installed packages:

```powershell
pip freeze > requirements.txt
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

---

# 🗃️ Database Backup

Create a PostgreSQL backup:

```powershell
pg_dump -U postgres -d vendora -F c -f backup.dump
```

Or SQL format:

```powershell
pg_dump -U postgres -d vendora > backup.sql
```

---

# ♻️ Database Restore

Restore SQL backup:

```powershell
psql -U postgres -d vendora -f backup.sql
```

For a custom-format dump:

```powershell
pg_restore -U postgres -d vendora backup.dump
```

> Always create a backup before performing destructive database operations.

---

## 5. Static Files Not Loading

Run:

```powershell
python manage.py collectstatic
```

Also verify:

```text
STATIC_URL
STATIC_ROOT
STATICFILES_DIRS
```

in `settings.py`.

---

## 6. Media Files Not Loading

During development, verify that your URL configuration serves media files when:

```python
DEBUG = True
```

Also verify:

```python
MEDIA_URL
MEDIA_ROOT
```

---

## 7. AI Assistant Timeout

If the AI assistant is slow or unavailable:

1. Make sure Ollama is running.
2. Check installed models:

```powershell
ollama list
```

3. Test the model:

```powershell
ollama run qwen2.5:3b
```

4. Verify:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

5. Check the Django terminal for AI-related errors.

---

## 8. AI Model Not Found

Pull the model:

```powershell
ollama pull qwen2.5:3b
```

Then:

```powershell
ollama list
```

Make sure the model name exactly matches your configuration.

---


# 📄 Environment Template

Create `.env.example`:

```env
DEBUG=True

SECRET_KEY=

ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=vendora
DB_USER=
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=5432

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

REDIS_URL=redis://127.0.0.1:6379/0

OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

---

# 📊 System Architecture

```text
                    ┌─────────────────────┐
                    │      Customer       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Vendora Frontend  │
                    │ Bootstrap + JS/AJAX │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Django Backend   │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
       PostgreSQL           Redis/Celery       AI Layer
             │                 │                 │
             │                 │                 ▼
             │                 │              Ollama
             │                 │                 │
             │                 │                 ▼
             │                 │          Semantic Search
             │                 │
             └─────────────────┴─────────────────┘
```

---

# 🔄 Application Architecture

```text
                    VENDORA
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   Accounts        Marketplace      Dashboard
        │              │              │
        │       ┌──────┼──────┐       │
        │       │      │      │       │
        ▼       ▼      ▼      ▼       ▼
      Users  Products Cart Orders   Reports
                 │       │      │
                 │       │      │
                 └───────┴──────┘
                         │
                         ▼
                     AI Assistant
```

---

# 🔗 Important URLs

Typical development URLs:

```text
Homepage
http://127.0.0.1:8000/

Admin
http://127.0.0.1:8000/admin/

Products
http://127.0.0.1:8000/products/

Cart
http://127.0.0.1:8000/cart/

Orders
http://127.0.0.1:8000/orders/

Dashboard
http://127.0.0.1:8000/dashboard/

AI Assistant
http://127.0.0.1:8000/ai/
```

> Update these URLs if your actual `urls.py` uses different routes.

---

# 📋 Development Checklist

After cloning the project:

```text
☐ Install Python
☐ Install PostgreSQL
☐ Install Redis
☐ Clone repository
☐ Create virtual environment
☐ Activate virtual environment
☐ Install requirements
☐ Create PostgreSQL database
☐ Create .env
☐ Run migrations
☐ Create superuser
☐ Collect static files
☐ Start Redis
☐ Start Celery
☐ Start Django
☐ Install Ollama (optional)
☐ Pull AI model (optional)
☐ Rebuild embeddings (optional)
☐ Test application
```
---

# 🧪 Testing

Run the Django test suite:

```powershell
python manage.py test
```

Run a specific application:

```powershell
python manage.py test apps.products
```

Run a specific test module:

```powershell
python manage.py test apps.products.tests
```

---

# 📜 License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this project according to the terms of the license.

---

# 👨‍💻 Author

**Moaz Jamil**

Full Stack Developer
Django / Web Development / Flutter / AI Integration

GitHub:

```text
https://github.com/moaz-jamil
```

---

# ⭐ Support

If you find Vendora useful or interesting:

⭐ Star the repository
🍴 Fork the project
🐛 Report bugs
💡 Suggest features
🤝 Contribute improvements

---

# 🛍️ Vendora

> **A modern multi-vendor marketplace designed to connect customers, companies, retailers and sellers through one powerful e-commerce platform.**

**Built with Django ❤️**
