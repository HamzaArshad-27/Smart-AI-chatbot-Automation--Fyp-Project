# Vendora

Vendora is a Django-based multi-vendor e-commerce marketplace with buyer, seller, company, retailer, and admin flows. The project includes product management, shopping cart, order workflows, dashboard pages, and an AI shopping assistant powered by Ollama.

## Project overview

- Multi-vendor marketplace platform
- Separate admin, company, seller, retailer, and customer dashboards
- PostgreSQL database configuration
- Bootstrap-based frontend
- AI assistant integration for product discovery and support
- Django authentication, OTP-based verification, and approval flow

## Tech stack

- Python 3.10+
- Django 5.2
- PostgreSQL 15+
- Redis (recommended for async/background tasks)
- Bootstrap 5
- Django Crispy Forms
- Pillow, OpenPyXL, NumPy, Pandas
- LangChain / LangGraph / FAISS / sentence-transformers
- Ollama for local AI model inference

## Project structure

```text
vendora/
├── apps/
│   ├── accounts/
│   ├── ai_assistant/
│   ├── cart/
│   ├── companies/
│   ├── core/
│   ├── dashboard/
│   ├── orders/
│   ├── products/
│   └── reports/
├── ai_embeddings/
├── docs/
├── media/
├── static/
├── templates/
├── vendora/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .gitignore
├── manage.py
├── requirements.txt
├── test_all.py
├── README.md
└── products.csv
```

## Prerequisites

Before running the project, install:

- Python 3.10 or newer
- PostgreSQL 15 or newer
- Redis server
- Ollama (for AI assistant features)
- Git

## 1) Clone the project

```powershell
git clone https://github.com/yourusername/vendora.git
cd vendora
```

## 2) Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If you are using Git Bash or Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3) Install dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

## 4) Set up PostgreSQL

Create a PostgreSQL database and user:

```sql
CREATE DATABASE vendora;
CREATE USER postgres WITH PASSWORD '123451';
ALTER USER postgres WITH SUPERUSER;
```

If you prefer a different database name/user/password, update the values in your environment file.

## 5) Configure environment variables

Create a `.env` file in the project root.

```powershell
copy .env.example .env
notepad .env
```

Example content:

```env
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
DEV_MODE=True
SITE_URL=http://127.0.0.1:8000
DB_NAME=vendora
DB_USER=postgres
DB_PASSWORD=123451
DB_HOST=localhost
DB_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT=60
```

> The settings file already reads these variables using `python-decouple`, so they must exist before running the app.

## 6) Run database migrations

```powershell
python manage.py migrate
```

If Django reports missing migrations for a local app, run:

```powershell
python manage.py makemigrations
python manage.py migrate
```

## 7) Create an admin user

```powershell
python manage.py createsuperuser
```

Then follow the prompts to create your superuser account.

## 8) Start the development server

```powershell
python manage.py runserver
```

Open the project in your browser:

- Home: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Login: http://127.0.0.1:8000/accounts/login/
- Dashboard: http://127.0.0.1:8000/dashboard/
- AI assistant: http://127.0.0.1:8000/ai/

## 9) AI assistant setup

This project includes an AI assistant that uses Ollama and vector embeddings.

Start Ollama:

```powershell
ollama serve
```

Pull the default model used in the settings:

```powershell
ollama pull qwen2.5:3b
```

If you want to inspect the local AI model settings, check `vendora/settings.py`.

## 10) Run tests

Run Django test suite:

```powershell
python manage.py test
```

Run the custom chatbot test script:

```powershell
python test_all.py
```

## Useful commands

```powershell
python manage.py check
python manage.py shell
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

## Common production notes

- Keep `DEBUG=False` in production.
- Set a safe `SECRET_KEY` in your `.env` file.
- Use a real SMTP provider for email delivery.
- Set `DEV_MODE=False` if you want stricter approval-based user registration.
- Redis is recommended if you enable background tasks or Celery workers later.

## License

This project is intended for academic/demo use unless you add your own license terms.

## Support

For setup issues, verify:

1. PostgreSQL is running and your database exists.
2. `.env` values are correct.
3. Python packages are installed in the active virtual environment.
4. Ollama is running when testing AI features.
