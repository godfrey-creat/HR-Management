# HRMS Backend Implementation
# File: app.py (Main Flask Application)

from flask import Flask, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from functools import wraps
import uuid

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hrms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # admin, manager, employee, recruiter
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    employee = db.relationship('Employee', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employees = db.relationship('Employee', backref='department', lazy=True)

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    position = db.Column(db.String(100))
    salary = db.Column(db.Numeric(10, 2))
    hire_date = db.Column(db.Date, default=datetime.utcnow().date)
    status = db.Column(db.String(20), default='active')  # active, inactive, terminated
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='employee', lazy=True)
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy=True)
    payroll_records = db.relationship('PayrollRecord', backref='employee', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'email': self.email,
            'phone': self.phone,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'position': self.position,
            'salary': float(self.salary) if self.salary else None,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'status': self.status,
            'manager_id': self.manager_id
        }

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    clock_in = db.Column(db.DateTime)
    clock_out = db.Column(db.DateTime)
    break_time = db.Column(db.Integer, default=0)  # minutes
    total_hours = db.Column(db.Numeric(4, 2))
    status = db.Column(db.String(20), default='present')  # present, absent, late, half_day
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(30), nullable=False)  # sick, vacation, maternity, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    approved_at = db.Column(db.DateTime)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PayrollRecord(db.Model):
    __tablename__ = 'payroll_records'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end = db.Column(db.Date, nullable=False)
    basic_salary = db.Column(db.Numeric(10, 2), nullable=False)
    allowances = db.Column(db.Numeric(10, 2), default=0)
    overtime_amount = db.Column(db.Numeric(10, 2), default=0)
    gross_pay = db.Column(db.Numeric(10, 2), nullable=False)
    tax_deduction = db.Column(db.Numeric(10, 2), default=0)
    other_deductions = db.Column(db.Numeric(10, 2), default=0)
    net_pay = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, processed, paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.role not in allowed_roles:
                return jsonify({'message': 'Access forbidden'}), 403
            
            g.current_user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# API ROUTES - AUTHENTICATION
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'employee')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User registered successfully', 'user': user.to_dict()}), 201
    
    except Exception as e:
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict()
            }), 200
        
        return jsonify({'message': 'Invalid credentials'}), 401
    
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 400

# ============================================================================
# API ROUTES - EMPLOYEE MANAGEMENT
# ============================================================================

@app.route('/api/employees', methods=['GET'])
@role_required('admin', 'manager')
def get_employees():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        employees = Employee.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'employees': [emp.to_dict() for emp in employees.items],
            'total': employees.total,
            'pages': employees.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to retrieve employees', 'error': str(e)}), 500

@app.route('/api/employees', methods=['POST'])
@role_required('admin')
def create_employee():
    try:
        data = request.get_json()
        
        # Generate employee ID
        emp_id = f"EMP{str(uuid.uuid4())[:8].upper()}"
        
        employee = Employee(
            employee_id=emp_id,
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data.get('phone'),
            department_id=data.get('department_id'),
            position=data.get('position'),
            salary=data.get('salary'),
            hire_date=datetime.strptime(data['hire_date'], '%Y-%m-%d').date() if data.get('hire_date') else datetime.utcnow().date(),
            manager_id=data.get('manager_id')
        )
        
        db.session.add(employee)
        db.session.commit()
        
        return jsonify({'message': 'Employee created successfully', 'employee': employee.to_dict()}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create employee', 'error': str(e)}), 400

@app.route('/api/employees/<int:employee_id>', methods=['GET'])
@role_required('admin', 'manager', 'employee')
def get_employee(employee_id):
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        # Check if employee can view this data
        if g.current_user.role == 'employee' and g.current_user.employee.id != employee_id:
            return jsonify({'message': 'Access forbidden'}), 403
        
        return jsonify({'employee': employee.to_dict()}), 200
    
    except Exception as e:
        return jsonify({'message': 'Employee not found', 'error': str(e)}), 404

# ============================================================================
# API ROUTES - ATTENDANCE MANAGEMENT
# ============================================================================

@app.route('/api/attendance/clock-in', methods=['POST'])
@role_required('employee', 'manager', 'admin')
def clock_in():
    try:
        data = request.get_json()
        employee_id = data.get('employee_id') or g.current_user.employee.id
        
        # Check if already clocked in today
        today = datetime.utcnow().date()
        existing = Attendance.query.filter_by(
            employee_id=employee_id, 
            date=today
        ).first()
        
        if existing and existing.clock_in:
            return jsonify({'message': 'Already clocked in today'}), 400
        
        if existing:
            existing.clock_in = datetime.utcnow()
            existing.status = 'present'
        else:
            attendance = Attendance(
                employee_id=employee_id,
                date=today,
                clock_in=datetime.utcnow(),
                status='present'
            )
            db.session.add(attendance)
        
        db.session.commit()
        return jsonify({'message': 'Clocked in successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': 'Clock in failed', 'error': str(e)}), 400

@app.route('/api/attendance/clock-out', methods=['POST'])
@role_required('employee', 'manager', 'admin')
def clock_out():
    try:
        data = request.get_json()
        employee_id = data.get('employee_id') or g.current_user.employee.id
        
        today = datetime.utcnow().date()
        attendance = Attendance.query.filter_by(
            employee_id=employee_id, 
            date=today
        ).first()
        
        if not attendance or not attendance.clock_in:
            return jsonify({'message': 'Must clock in first'}), 400
        
        if attendance.clock_out:
            return jsonify({'message': 'Already clocked out today'}), 400
        
        attendance.clock_out = datetime.utcnow()
        
        # Calculate total hours
        time_diff = attendance.clock_out - attendance.clock_in
        total_minutes = time_diff.total_seconds() / 60 - attendance.break_time
        attendance.total_hours = round(total_minutes / 60, 2)
        
        db.session.commit()
        return jsonify({'message': 'Clocked out successfully', 'total_hours': float(attendance.total_hours)}), 200
    
    except Exception as e:
        return jsonify({'message': 'Clock out failed', 'error': str(e)}), 400

# ============================================================================
# API ROUTES - LEAVE MANAGEMENT
# ============================================================================

@app.route('/api/leave-requests', methods=['GET'])
@role_required('employee', 'manager', 'admin')
def get_leave_requests():
    try:
        if g.current_user.role == 'employee':
            # Employee can only see their own requests
            requests = LeaveRequest.query.filter_by(employee_id=g.current_user.employee.id).all()
        else:
            # Managers and admins can see all requests
            requests = LeaveRequest.query.all()
        
        return jsonify({
            'leave_requests': [{
                'id': req.id,
                'employee_name': f"{req.employee.first_name} {req.employee.last_name}",
                'leave_type': req.leave_type,
                'start_date': req.start_date.isoformat(),
                'end_date': req.end_date.isoformat(),
                'days_requested': req.days_requested,
                'reason': req.reason,
                'status': req.status,
                'created_at': req.created_at.isoformat()
            } for req in requests]
        }), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to retrieve leave requests', 'error': str(e)}), 500

@app.route('/api/leave-requests', methods=['POST'])
@role_required('employee', 'manager', 'admin')
def create_leave_request():
    try:
        data = request.get_json()
        
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        days_requested = (end_date - start_date).days + 1
        
        leave_request = LeaveRequest(
            employee_id=g.current_user.employee.id,
            leave_type=data['leave_type'],
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=data.get('reason', '')
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        return jsonify({'message': 'Leave request submitted successfully'}), 201
    
    except Exception as e:
        return jsonify({'message': 'Failed to create leave request', 'error': str(e)}), 400

# ============================================================================
# API ROUTES - DEPARTMENTS
# ============================================================================

@app.route('/api/departments', methods=['GET'])
@role_required('admin', 'manager')
def get_departments():
    try:
        departments = Department.query.all()
        return jsonify({
            'departments': [{
                'id': dept.id,
                'name': dept.name,
                'description': dept.description,
                'employee_count': len(dept.employees)
            } for dept in departments]
        }), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to retrieve departments', 'error': str(e)}), 500

@app.route('/api/departments', methods=['POST'])
@role_required('admin')
def create_department():
    try:
        data = request.get_json()
        
        department = Department(
            name=data['name'],
            description=data.get('description', ''),
            manager_id=data.get('manager_id')
        )
        
        db.session.add(department)
        db.session.commit()
        
        return jsonify({'message': 'Department created successfully'}), 201
    
    except Exception as e:
        return jsonify({'message': 'Failed to create department', 'error': str(e)}), 400

# ============================================================================
# API ROUTES - DASHBOARD & REPORTS
# ============================================================================

@app.route('/api/dashboard/stats', methods=['GET'])
@role_required('admin', 'manager')
def get_dashboard_stats():
    try:
        total_employees = Employee.query.filter_by(status='active').count()
        present_today = Attendance.query.filter_by(
            date=datetime.utcnow().date(),
            status='present'
        ).count()
        pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
        total_departments = Department.query.count()
        
        return jsonify({
            'total_employees': total_employees,
            'present_today': present_today,
            'pending_leaves': pending_leaves,
            'total_departments': total_departments,
            'attendance_rate': round((present_today / total_employees * 100), 2) if total_employees > 0 else 0
        }), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to retrieve dashboard stats', 'error': str(e)}), 500

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Initialize database with sample data"""
    db.create_all()
    
    # Create admin user if doesn't exist
    if not User.query.filter_by(email='admin@hrms.com').first():
        admin_user = User(
            username='admin',
            email='admin@hrms.com',
            role='admin'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # Create sample department
        hr_dept = Department(name='Human Resources', description='HR Department')
        db.session.add(hr_dept)
        
        db.session.commit()
        
        # Create admin employee record
        admin_employee = Employee(
            employee_id='EMP00001',
            user_id=admin_user.id,
            first_name='System',
            last_name='Administrator',
            email='admin@hrms.com',
            department_id=hr_dept.id,
            position='HR Admin',
            salary=50000.00
        )
        db.session.add(admin_employee)
        db.session.commit()
        
        print("✅ Database initialized with admin user (admin@hrms.com / admin123)")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'message': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'message': 'Invalid token'}), 401

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    app.run(debug=True, host='0.0.0.0', port=5000)