# Flado

Flado is the usual todo list app project everyone does once (or more) in their lives, here built with Python, Flask, and SQLite.

I hacked it overnight, mainly to refresh my (very poor) frontend skills.

## Highlights

- Minimal, responsive UI on desktop and mobile.
- Fast task capture with inline editing and keyboard shortcuts.
- Smart filters for today, upcoming, completed, and custom views.
- SQLite-powered persistence with a lightweight schema that is easy to deploy anywhere.
- Uses Flask-WTF for CSRF protection.
- Clean Flask blueprints and service layers.

## Quick Start (for development)

```bash
# 1. Install and use uv (https://github.com/astral-sh/uv)
uv sync  # creates/updates .venv and installs dependencies

# 2. Set environment variables for Flask
export FLASK_APP=flado.app:create_app
export FLASK_ENV=development

# 3. Initialize the SQLite database (instance/flado.sqlite by default)
uv run flask db init
uv run flask db migrate -m "Initial migration"
uv run flask db upgrade

# 4. Run the development server
uv run flask run --debug
```

The SQLite database file is stored in the `instance/` directory (it remains outside of version control by default).

## Configuration

Environment variables can tweak runtime behavior:

- `FLASK_ENV`: Set to `development` or `production`.
- `FLADO_DATABASE_URI`: Override the default SQLite path (`sqlite:///instance/flado.sqlite`).
- `FLADO_SECRET_KEY`: Provide a secret key for session cookies.
- `FLADO_THEME`: Switch between built-in themes such as `light`, `dark`, or `auto`.

So you can create a `.env` file if you want:

```bash
cp .env.example .env
```

Note that `FLADO_SECRET_KEY` is **mandatory in production mode** (when not running in debug mode).

## Usage

- **Add tasks:** Use the quick-add form at the top of the list and press <kbd>Enter</kbd> to save it instantly.
- **Organize:** Drag and drop to reorder, toggle completion with a single click, and assign due dates or notes in the details panel.
- **Focus:** Switch to _Today_ or _Upcoming_ filters to keep attention on what matters.

## Project Structure

```
flado/
├── flado/                    # Main application package
│   ├── app.py                # Flask app factory/entry point
│   ├── blueprints.py         # Blueprint registration and routes
│   ├── models.py             # SQLAlchemy models
│   ├── services.py           # Business logic helpers
│   └── templates/            # Jinja2 HTML templates
├── instance/                 # Instance directory (SQLite DB lives here)
├── migrations/               # Alembic migration files
├── static/                   # CSS, JS, images, favicon, etc.
├── Dockerfile                # Docker build file
├── .env.example              # Example environment config for Docker/production
├── README.md                 # This file
├── pyproject.toml            # Python project configuration
├── uv.lock                   # UV lock file
└── wsgi.py                   # WSGI entry point for production deployment (optional)
```

## Deployment

If you want to deploy this on your own VPS because you love this application so much (it's your right), then you can use the Dockerfile to build the Docker image:

```bash
docker build -t flado .
```

And run the container either in the most simple way (`FLADO_SECRET_KEY` is mandatory in production mode):

```bash
docker run --name flado -d -p 5000:5000 -e FLADO_SECRET_KEY=your-secret-key flado
```

To use environment variables from `.env`:

```bash
docker run --name flado -d -p 5000:5000 --env-file .env flado
```

To use just one variable without `.env`:

```bash
docker run --name flado -d -p 5000:5000 -e FLADO_THEME=dark flado
```

To use a volume to persist the database:

```bash
docker run --name flado -d -p 5000:5000 -v flado-data:/app/instance flado
```

Because Flado relies on SQLite, you can deploy on small VPS instances or use `sqlite3` backups to keep data portable.

## Gunicorn (production)

If you want to use Gunicorn to serve the application, setup `.env` with a `FLADO_SECRET_KEY` and use the following command:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 --access-logfile - --error-logfile - wsgi:app
```

This will start the application with 2 workers and a timeout of 120 seconds.

## License

This project is released under the [BSD 3-Clause License](LICENSE).
