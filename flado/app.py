"""Flask application factory."""
import logging
import os
from typing import Optional, Tuple

from flask import Flask, jsonify, Response
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError
from dotenv import load_dotenv

from .blueprints import tasks_blueprint
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
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    template_dir = os.path.join(base_dir, 'flado', 'templates')
    static_dir = os.path.join(base_dir, 'static')

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
        instance_dir = os.path.join(base_dir, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        database_path = os.path.join(instance_dir, 'flado.sqlite')
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
    csrf.exempt('tasks.health_check')

    # Register error handlers
    @app.errorhandler(400)
    def bad_request(error) -> Tuple[Response, int]:
        """Handle 400 errors with JSON response."""
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400

    @app.errorhandler(404)
    def not_found(error) -> Tuple[Response, int]:
        """Handle 404 errors with JSON response."""
        return jsonify({'error': 'Not found', 'message': str(error)}), 404

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e) -> Tuple[Response, int]:
        """Handle CSRF errors with JSON response."""
        app.logger.warning(f'CSRF error: {e}')
        return jsonify({'error': 'CSRF token missing or invalid'}), 400

    @app.errorhandler(500)
    def internal_error(error) -> Tuple[Response, int]:
        """Handle 500 errors with JSON response."""
        app.logger.error(f'Server error: {error}')
        return jsonify({'error': 'Internal server error'}), 500

    # Register blueprints
    app.register_blueprint(tasks_blueprint)

    return app
