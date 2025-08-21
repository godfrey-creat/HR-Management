"""
Custom decorators for People360
"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.has_role('admin'):
            flash('You do not have permission to access this page.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def hr_required(f):
    """Decorator to require HR access (admin or hr_manager)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.can_access_hr():
            flash('You do not have permission to access HR features.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def crm_required(f):
    """Decorator to require CRM access (admin, sales_manager, or support_agent)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.can_access_crm():
            flash('You do not have permission to access CRM features.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login'))
            
            if not current_user.has_any_role(*roles):
                flash(f'You need one of these roles: {", ".join(roles)}.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator