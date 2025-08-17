# ============================================================================
# File: app/api/__init__.py
# API Blueprint Registration
# ============================================================================

from flask import Blueprint

def register_blueprints(app):
    """Register all API blueprints"""
    from .auth import auth_bp
    from .employees import employees_bp
    from .attendance import attendance_bp
    from .leave import leave_bp
    #from .departments import departments_bp
    #from .dashboard import dashboard_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(employees_bp, url_prefix='/api/employees')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(leave_bp, url_prefix='/api/leave')
    #app.register_blueprint(departments_bp, url_prefix='/api/departments')
    #app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')