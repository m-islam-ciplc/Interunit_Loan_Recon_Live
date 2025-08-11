"""
Interunit Loan Reconciliation - Main Flask Application
Modular architecture with service-based backend and route blueprints.
"""
import os
from flask import Flask
from core.routes import register_blueprints

app = Flask(__name__)

# Create upload folder
os.makedirs('uploads', exist_ok=True)

# Register all route blueprints (UI + API)
register_blueprints(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
    