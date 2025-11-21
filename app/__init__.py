"""
Flask Application for Email Outreach Platform
"""
from flask import Flask
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    CORS(app)
    
    # Register blueprints
    from app.api import campaigns, smtp_accounts, contacts, templates, dashboard
    app.register_blueprint(campaigns.bp)
    app.register_blueprint(smtp_accounts.bp)
    app.register_blueprint(contacts.bp)
    app.register_blueprint(templates.bp)
    app.register_blueprint(dashboard.bp)
    
    # Register main routes
    from app import routes
    app.register_blueprint(routes.bp)
    
    return app

