# ============================================================================
# File: app/utils/decorators.py
# Authentication and Authorization Decorators
# ============================================================================

from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import User

def role_required(*allowed_roles):
    """
    Decorator to check if user has required role
    Usage: @role_required('admin', 'manager')
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({'message': 'User account is inactive'}), 403
            
            if user.role not in allowed_roles:
                return jsonify({'message': 'Access forbidden. Required roles: ' + ', '.join(allowed_roles)}), 403
            
            g.current_user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def employee_or_manager_required(f):
    """
    Decorator that allows employees to access their own data or managers/admins to access any data
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(employee_id=None, *args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'message': 'User account is inactive'}), 403
        
        # Admins and managers can access any employee data
        if user.role in ['admin', 'manager']:
            g.current_user = user
            return f(employee_id, *args, **kwargs)
        
        # Employees can only access their own data
        if user.role == 'employee' and user.employee:
            if employee_id and str(user.employee.id) != str(employee_id):
                return jsonify({'message': 'Access forbidden'}), 403
            g.current_user = user
            return f(employee_id or user.employee.id, *args, **kwargs)
        
        return jsonify({'message': 'Access forbidden'}), 403
    return decorated_function