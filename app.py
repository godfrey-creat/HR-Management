# HRMS Backend Implementation
# File: app.py (Main Flask Application)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///hrms.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Import models so SQLAlchemy is aware of them
from app.models.models import Employee, User, Department, Attendance

# Import and register blueprints
from app.api.employees import employees_bp
from app.api.auth import auth_bp
from app.api.attendance import attendance_bp
from app.api.leave import leave_bp

app.register_blueprint(employees_bp, url_prefix="/api/employees")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
app.register_blueprint(leave_bp, url_prefix="/api/leave")

# Database initialization
def init_db():
    db.create_all()

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
