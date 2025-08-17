# ============================================================================
# DATABASE MODELS + LEAVE MANAGEMENT LOGIC
# ============================================================================
from datetime import datetime, date
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize (⚠️ DO NOT pass app here, bind later in app.py)
db = SQLAlchemy()


# -----------------------------
# User & Employee
# -----------------------------
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


# -----------------------------
# Leave Management
# -----------------------------
class LeaveType(Enum):
    SICK = "sick"
    VACATION = "vacation"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    UNPAID = "unpaid"


class LeaveStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.Enum(LeaveType), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.Enum(LeaveStatus), default=LeaveStatus.PENDING)
    approved_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    approved_at = db.Column(db.DateTime)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -----------------------------
# Payroll
# -----------------------------
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


# -----------------------------
# Leave Manager (Business Logic)
# -----------------------------
class LeaveManager:
    """Handles leave application logic using SQLAlchemy."""

    @staticmethod
    def apply_leave(employee_id, leave_type: LeaveType, start_date: date, end_date: date, reason=""):
        days = (end_date - start_date).days + 1
        leave = LeaveRequest(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            days_requested=days,
            reason=reason,
            status=LeaveStatus.PENDING
        )
        db.session.add(leave)
        db.session.commit()
        return leave

    @staticmethod
    def approve_leave(leave_id, manager_id):
        leave = LeaveRequest.query.get(leave_id)
        if leave and leave.status == LeaveStatus.PENDING:
            leave.status = LeaveStatus.APPROVED
            leave.approved_by = manager_id
            leave.approved_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def reject_leave(leave_id, manager_id, comments=""):
        leave = LeaveRequest.query.get(leave_id)
        if leave and leave.status == LeaveStatus.PENDING:
            leave.status = LeaveStatus.REJECTED
            leave.approved_by = manager_id
            leave.approved_at = datetime.utcnow()
            leave.comments = comments
            db.session.commit()
            return True
        return False

    @staticmethod
    def cancel_leave(leave_id):
        leave = LeaveRequest.query.get(leave_id)
        if leave and leave.status == LeaveStatus.PENDING:
            leave.status = LeaveStatus.CANCELLED
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_leave_balance(employee_id):
        # Simplified: count approved leaves by type
        balances = {}
        for leave_type in LeaveType:
            count = LeaveRequest.query.filter_by(
                employee_id=employee_id, leave_type=leave_type, status=LeaveStatus.APPROVED
            ).count()
            balances[leave_type.value] = count
        return balances

    @staticmethod
    def get_employee_applications(employee_id):
        return LeaveRequest.query.filter_by(employee_id=employee_id).all()

    @staticmethod
    def get_pending_applications():
        return LeaveRequest.query.filter_by(status=LeaveStatus.PENDING).all()
