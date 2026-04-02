# Tax Automation Backend

Django REST API for the Tax Automation Portal.

---

## Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
# 1. Clone the repo and navigate to backend
cd backend

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and set your values (SECRET_KEY, DEBUG=True for local, etc.)

# 5. Apply migrations
python manage.py migrate

# 6. Create initial data (tax year + default consultant account)
python manage.py shell < create_initial_data.py

# 7. Run the development server
python manage.py runserver
```

Default consultant login: `consultant@taxportal.lk` / `Admin@12345`

API base URL: `http://localhost:8000/api/`  
Admin panel: `http://localhost:8000/admin/`

---

## Hosting on Render

### Option 1 — render.yaml (recommended)

`render.yaml` in this repo defines both the web service and a PostgreSQL database.  
Render will read it automatically when you connect the repo.

**Steps:**

1. Push this repo to GitHub (or GitLab).
2. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Connect your repository. Render detects `render.yaml` and shows a preview of the resources it will create:
   - `tax-automation-backend` — Python web service
   - `tax-automation-db` — PostgreSQL database (free tier)
4. Click **Apply**. Render will:
   - Provision the database
   - Run `build.sh` (installs deps, runs `collectstatic` and `migrate`)
   - Start the server with Gunicorn
5. Once deployed, set the remaining environment variables in the Render dashboard under the service's **Environment** tab:

   | Key | Value |
   |-----|-------|
   | `CORS_ALLOWED_ORIGINS` | Your frontend URL, e.g. `https://your-app.onrender.com` |
   | `EMAIL_HOST_USER` | Your Gmail address |
   | `EMAIL_HOST_PASSWORD` | Your Gmail App Password |
   | `DEFAULT_FROM_EMAIL` | Sender address |

6. Create the initial consultant account via the Render **Shell** tab:

   ```bash
   python manage.py shell < create_initial_data.py
   ```

### Option 2 — Manual setup

1. **Create a PostgreSQL database** on Render (New → PostgreSQL). Copy the **Internal Database URL**.

2. **Create a Web Service** (New → Web Service), connect your repo, and set:

   | Field | Value |
   |-------|-------|
   | Runtime | Python |
   | Build Command | `./build.sh` |
   | Start Command | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |

3. Add the following **Environment Variables** in the service settings:

   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | A strong random string (use Render's "Generate" button) |
   | `DEBUG` | `False` |
   | `DATABASE_URL` | Internal Database URL from step 1 |
   | `ALLOWED_HOSTS` | `localhost,127.0.0.1` (Render hostname is added automatically) |
   | `CORS_ALLOWED_ORIGINS` | Your frontend URL |
   | `EMAIL_HOST_USER` | Gmail address |
   | `EMAIL_HOST_PASSWORD` | Gmail App Password |

4. Click **Deploy**. After the first deploy, seed the database:

   ```bash
   # Render Shell tab (or one-off job)
   python manage.py shell < create_initial_data.py
   ```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | insecure default | Django secret key |
| `DEBUG` | No | `False` | Set `True` for local dev only |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated hostnames |
| `DATABASE_URL` | Prod | SQLite fallback | Full PostgreSQL connection string |
| `CORS_ALLOWED_ORIGINS` | Yes | localhost origins | Comma-separated frontend URLs |
| `EMAIL_BACKEND` | No | console | `django.core.mail.backends.smtp.EmailBackend` for real email |
| `EMAIL_HOST` | No | `smtp.gmail.com` | SMTP server |
| `EMAIL_PORT` | No | `587` | SMTP port |
| `EMAIL_USE_TLS` | No | `True` | Enable TLS |
| `EMAIL_HOST_USER` | No | — | SMTP username |
| `EMAIL_HOST_PASSWORD` | No | — | SMTP password / app password |
| `DEFAULT_FROM_EMAIL` | No | `noreply@taxautomation.lk` | Sender address |

---

## API Endpoints

| Prefix | App | Description |
|--------|-----|-------------|
| `/api/auth/` | authentication | Register, login, logout, token refresh |
| `/api/clients/` | clients | Client management |
| `/api/tax/` | tax_forms | Tax forms and calculations |
| `/api/documents/` | documents | Document upload/download |
| `/api/notifications/` | notifications | User notifications |
| `/admin/` | — | Django admin panel |
