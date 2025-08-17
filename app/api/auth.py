# ============================================================================
# File: app/api/auth.py
# Authentication Routes
# ============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.models import User, Employee, db
from app.utils.helpers import validate_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'message': 'Invalid email format'}), 400
        
        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'].strip(),
            email=data['email'].strip().lower(),
            role=data.get('role', 'employee')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password are required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=data['email'].strip().lower()).first()
        
        if user and user.check_password(data['password']) and user.is_active:
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Get employee data if exists
            employee_data = None
            if user.employee:
                employee_data = user.employee.to_dict()
            
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict(),
                'employee': employee_data
            }), 200
        
        return jsonify({'message': 'Invalid credentials'}), 401
    
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        employee_data = None
        if user.employee:
            employee_data = user.employee.to_dict()
        
        return jsonify({
            'user': user.to_dict(),
            'employee': employee_data
        }), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to get user info', 'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Validate old password
        if not user.check_password(data['old_password']):
            return jsonify({'message': 'Current password is incorrect'}), 400
        
        # Update password
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to change password', 'error': str(e)}), 500