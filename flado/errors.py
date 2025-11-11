"""Error handlers for Flask application."""
from typing import Tuple
from flask import Flask, jsonify, Response
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    """Register all error handlers with the Flask app."""

    @app.errorhandler(400)
    def bad_request(error: HTTPException) -> Tuple[Response, int]:
        """Handle 400 errors with JSON response."""
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400

    @app.errorhandler(404)
    def not_found(error: HTTPException) -> Tuple[Response, int]:
        """Handle 404 errors with JSON response."""
        return jsonify({'error': 'Not found', 'message': str(error)}), 404

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError) -> Tuple[Response, int]:
        """Handle CSRF errors with JSON response."""
        app.logger.warning(f'CSRF error: {e}')
        return jsonify({'error': 'CSRF token missing or invalid'}), 400

    @app.errorhandler(500)
    def internal_error(error: Exception) -> Tuple[Response, int]:
        """Handle 500 errors with JSON response."""
        app.logger.error(f'Server error: {error}')
        return jsonify({'error': 'Internal server error'}), 500
