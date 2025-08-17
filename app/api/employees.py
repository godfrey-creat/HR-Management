# ============================================================================
# File: app/api/employees.py
# Employee Management Routes
# ============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid
from app.models.models import Employee, User, Department, Attendance, db
from app.utils.decorators import role_required
from app.utils.helpers import generate_employee_id, validate_email

employees_bp = Blueprint('employees', __name__)

# ---------------------- GET EMPLOYEES ----------------------
@employees_bp.route('/', methods=['GET'])
@role_required('admin', 'manager')
def get_employees():
    """Get list of employees with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)  # Limit max per_page
        search = request.args.get('search', '').strip()
        department_id = request.args.get('department_id', type=int)
        status = request.args.get('status', 'active')
        
        query = Employee.query
        
        # Apply filters
        if search:
            query = query.filter(
                db.or_(
                    Employee.first_name.contains(search),
                    Employee.last_name.contains(search),
                    Employee.email.contains(search),
                    Employee.employee_id.contains(search)
                )
            )
        
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        
        if status:
            query = query.filter(Employee.status == status)
        
        # Paginate results
        employees = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'employees': [emp.to_dict() for emp in employees.items],
            'total': employees.total,
            'pages': employees.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to retrieve employees', 'error': str(e)}), 500

# ---------------------- CREATE EMPLOYEE ----------------------
@employees_bp.route('/', methods=['POST'])
@role_required('admin')
def create_employee():
    """Create a new employee"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'message': 'Invalid email format'}), 400
        
        # Check if email already exists
        if Employee.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Employee email already exists'}), 400
        
        # Generate employee ID
        employee_id = generate_employee_id()
        
        # Parse hire date if provided
        hire_date = datetime.utcnow().date()
        if data.get('hire_date'):
            try:
                hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'message': 'Invalid hire_date format. Use YYYY-MM-DD'}), 400
        
        # Create employee
        employee = Employee(
            employee_id=employee_id,
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            email=data['email'].strip().lower(),
            phone=data.get('phone', '').strip(),
            department_id=data.get('department_id'),
            position=data.get('position', '').strip(),
            salary=data.get('salary'),
            hire_date=hire_date,
            manager_id=data.get('manager_id'),
            status='active'
        )
        
        db.session.add(employee)
        db.session.commit()
        
        return jsonify({
            'message': 'Employee created successfully',
            'employee': employee.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create employee', 'error': str(e)}), 500

# ---------------------- GET SINGLE EMPLOYEE ----------------------
@employees_bp.route('/<int:employee_id>', methods=['GET'])
@jwt_required()
def get_employee(employee_id):
    """Get employee details"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'message': 'User not found'}), 404
        
        employee = Employee.query.get_or_404(employee_id)
        
        # Check access permissions
        if current_user.role == 'employee':
            # Employees can only view their own data
            if not current_user.employee or current_user.employee.id != employee_id:
                return jsonify({'message': 'Access forbidden'}), 403
        
        return jsonify({'employee': employee.to_dict()}), 200
    
    except Exception as e:
        return jsonify({'message': 'Employee not found', 'error': str(e)}), 404

# ---------------------- UPDATE EMPLOYEE ----------------------
@employees_bp.route('/<int:employee_id>', methods=['PUT'])
@role_required('admin')
def update_employee(employee_id):
    """Update employee information"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'first_name' in data:
            employee.first_name = data['first_name'].strip()
        if 'last_name' in data:
            employee.last_name = data['last_name'].strip()
        if 'email' in data:
            # Check if new email is already taken by another employee
            existing = Employee.query.filter(
                Employee.email == data['email'].strip().lower(),
                Employee.id != employee_id
            ).first()
            if existing:
                return jsonify({'message': 'Email already exists'}), 400
            employee.email = data['email'].strip().lower()
        if 'phone' in data:
            employee.phone = data['phone'].strip()
        if 'department_id' in data:
            employee.department_id = data['department_id']
        if 'position' in data:
            employee.position = data['position'].strip()
        if 'salary' in data:
            employee.salary = data['salary']
        if 'manager_id' in data:
            employee.manager_id = data['manager_id']
        if 'status' in data:
            employee.status = data['status']
        
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Employee updated successfully',
            'employee': employee.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update employee', 'error': str(e)}), 500

# ---------------------- DELETE EMPLOYEE ----------------------
@employees_bp.route('/<int:employee_id>', methods=['DELETE'])
@role_required('admin')
def delete_employee(employee_id):
    """Soft delete an employee"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        employee.status = 'terminated'
        employee.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Employee terminated successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to terminate employee', 'error': str(e)}), 500

# ---------------------- GET ATTENDANCE STATUS ----------------------
@employees_bp.route('/attendance/status', methods=['GET'])
@jwt_required()
def get_attendance_status():
    """Get current attendance status"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.employee:
            return jsonify({'message': 'Employee record not found'}), 404
        
        today = datetime.utcnow().date()
        attendance = Attendance.query.filter_by(
            employee_id=current_user.employee.id,
            date=today
        ).first()
        
        if not attendance:
            return jsonify({
                'status': 'not_clocked_in',
                'clock_in': None,
                'clock_out': None,
                'total_hours': None
            }), 200
        
        status = 'clocked_in' if attendance.clock_in and not attendance.clock_out else 'clocked_out'
        
        return jsonify({
            'status': status,
            'clock_in': attendance.clock_in.isoformat() if attendance.clock_in else None,
            'clock_out': attendance.clock_out.isoformat() if attendance.clock_out else None,
            'total_hours': float(attendance.total_hours) if attendance.total_hours else None
        }), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to get attendance status', 'error': str(e)}), 500
