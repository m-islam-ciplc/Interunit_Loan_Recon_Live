"""
Routes module - Organizes all API endpoints into logical blueprints.
"""
from flask import Blueprint

# Import all route blueprints
from .upload_routes import upload_bp
from .data_routes import data_bp
from .reconciliation_routes import reconciliation_bp
from .export_routes import export_bp
from .management_routes import management_bp
from .ui_routes import ui_bp

# Register blueprints
def register_blueprints(app):
    """Register all route blueprints with the Flask app."""
    # UI routes without API prefix
    app.register_blueprint(ui_bp)

    # API routes
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(data_bp, url_prefix='/api')
    app.register_blueprint(reconciliation_bp, url_prefix='/api')
    app.register_blueprint(export_bp, url_prefix='/api')
    app.register_blueprint(management_bp, url_prefix='/api') 