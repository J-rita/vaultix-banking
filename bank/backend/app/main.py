import os
from dotenv import load_dotenv

"""
Vaultix Enterprise Banking System - Core Application Entry Point
This module initializes the Flask application, loads environment variables,
configures CORS and JWT, and registers all API blueprints. It also serves
the frontend application files, providing a unified full-stack architecture.
"""

# Load .env file from the backend directory before anything else
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

from flask import Flask, send_from_directory, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from .routes import auth, accounts, transactions, admin, loans, notifications
from .auth.security import bcrypt

def create_app():
    # Set up the base directory for pathing
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    frontend_dir = os.path.join(base_dir, "frontend")
    static_dir = os.path.join(frontend_dir, "static")

    app = Flask(__name__, 
                static_folder=static_dir,
                template_folder=frontend_dir)

    # Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv("SECRET_KEY", "vaultix-premium-secret-8822")
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600 # 1 hour

    # Initialize extensions
    bcrypt.init_app(app)
    CORS(app)
    jwt = JWTManager(app)

    @app.before_request
    def log_request_info():
        print(f"[REQUEST] {request.method} {request.path}")

    # Register Blueprints
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(accounts.bp, url_prefix='/api/accounts')
    app.register_blueprint(transactions.bp, url_prefix='/api/transactions')
    app.register_blueprint(admin.bp, url_prefix='/api/admin')
    app.register_blueprint(loans.bp, url_prefix='/api/loans')
    app.register_blueprint(notifications.bp, url_prefix='/api/notifications')

    # Serving the Frontend
    @app.route('/')
    def serve_index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/<path:page>')
    def serve_page(page):
        # Ensure we only serve .html files or specific patterns
        if page.endswith('.html'):
            return send_from_directory(frontend_dir, page)
        # Fallback to .html for simple paths
        if '.' not in page:
             return send_from_directory(frontend_dir, f"{page}.html")
        return send_from_directory(frontend_dir, page)

    @app.after_request
    def add_header(response):
        # Prevent caching for all routes
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
