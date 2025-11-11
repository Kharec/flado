"""Flask application factory."""
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from .blueprints import health_check, tasks_blueprint
from .errors import register_error_handlers
from .models import db

# Determine if we're in production
FLASK_ENV = os.getenv('FLASK_ENV', 'development').lower()
_is_production = FLASK_ENV == 'production'


def setup_logging(app: Flask) -> None:
    """Configure logging for the application."""
    if not app.debug and not app.testing:
        app.logger.setLevel(logging.INFO)
    else:
        app.logger.setLevel(logging.DEBUG)


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application factory pattern for Flask.

    Args:
        config_name: Optional configuration name (development, production, etc.)

    Returns:
        Flask application instance
    """
    # Load environment variables
    load_dotenv()

    # Get the base directory (project root)
    base_dir = Path(__file__).parent.parent.resolve()
    template_dir = base_dir / 'flado' / 'templates'
    static_dir = base_dir / 'static'
    app = Flask(__name__, template_folder=template_dir,
                static_folder=static_dir)

    # Secret key handling
    secret_key = os.getenv('FLADO_SECRET_KEY')
    if not secret_key:
        if _is_production:
            raise ValueError(
                "FLADO_SECRET_KEY environment variable must be set in production")
        app.logger.warning("Using default secret key - change in production")
        secret_key = 'dev-secret-key-change-in-production'
    app.config['SECRET_KEY'] = secret_key

    # Database configuration
    database_uri = os.getenv('FLADO_DATABASE_URI')
    if not database_uri:
        instance_dir = base_dir / 'instance'
        instance_dir.mkdir(exist_ok=True)
        database_path = instance_dir / 'flado.sqlite'
        database_uri = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Validate database URI format
    if not database_uri.startswith(('sqlite:///')):
        raise ValueError(f"Invalid database URI format: {database_uri}")

    # Theme configuration
    app.config['FLADO_THEME'] = os.getenv('FLADO_THEME', 'auto')

    # Session configuration for CSRF protection
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    if _is_production:
        app.config['SESSION_COOKIE_SECURE'] = True

    # Setup logging
    setup_logging(app)

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    csrf = CSRFProtect(app)

    # Exempt health check endpoint from CSRF (used by monitoring)
    csrf.exempt(health_check)

    # Register blueprints
    app.register_blueprint(tasks_blueprint)

    # Register error handlers
    register_error_handlers(app)

    return app
