"""
Employee model for HR management
"""

from datetime import datetime
from app import db

class Employee(db.Model):
    """Employee model for HR management"""
    
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    
    # Job Information
    department = db.Column(db.String(50))
    position = db.Column(db.String(100), nullable=False)
    hire_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    employment_type = db.Column(db.String(20), default='full_time')  # full_time, part_time, contract, intern
    status = db.Column(db.String(20), default='active')  # active, inactive, terminated
    
    # Compensation
    salary = db.Column(db.Numeric(10, 2))
    salary_type = db.Column(db.String(20), default='monthly')  # hourly, monthly, yearly
    
    # Manager and Reporting
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    manager = db.relationship('Employee', remote_side=[id], backref='direct_reports')
    
    # System fields
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Files and documents
    resume_path = db.Column(db.String(200))
    photo_path = db.Column(db.String(200))
    
    # Employment status constants
    EMPLOYMENT_TYPES = {
        'full_time': 'Full Time',
        'part_time': 'Part Time',
        'contract': 'Contract',
        'intern': 'Intern'
    }
    
    STATUSES = {
        'active': 'Active',
        'inactive': 'Inactive',
        'terminated': 'Terminated',
        'on_leave': 'On Leave'
    }
    
    def __repr__(self):
        return f'<Employee {self.employee_id}: {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        """Get employee's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_employment_type_display(self):
        """Get human-readable employment type"""
        return self.EMPLOYMENT_TYPES.get(self.employment_type, self.employment_type.title())
    
    def get_status_display(self):
        """Get human-readable status"""
        return self.STATUSES.get(self.status, self.status.title())
    
    def years_of_service(self):
        """Calculate years of service"""
        if self.hire_date:
            today = datetime.utcnow().date()
            return (today - self.hire_date).days / 365.25
        return 0
    
    def is_active(self):
        """Check if employee is active"""
        return self.status == 'active'
    
    def get_manager_name(self):
        """Get manager's full name"""
        if self.manager:
            return self.manager.full_name
        return None
    
    def to_dict(self):
        """Convert employee to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'department': self.department,
            'position': self.position,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'employment_type': self.employment_type,
            'employment_type_display': self.get_employment_type_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'salary': float(self.salary) if self.salary else None,
            'manager_name': self.get_manager_name(),
            'years_of_service': round(self.years_of_service(), 1),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TimeOff(db.Model):
    """Time off requests and tracking"""
    
    __tablename__ = 'time_off'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    employee = db.relationship('Employee', backref='time_off_requests')
    
    # Request details
    request_type = db.Column(db.String(20), nullable=False)  # vacation, sick, personal, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text)
    
    # Status and approval
    status = db.Column(db.String(20), default='pending')  # pending, approved, denied
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approver = db.relationship('User')
    approved_at = db.Column(db.DateTime)
    comments = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    REQUEST_TYPES = {
        'vacation': 'Vacation',
        'sick': 'Sick Leave',
        'personal': 'Personal',
        'maternity': 'Maternity',
        'paternity': 'Paternity',
        'bereavement': 'Bereavement'
    }
    
    STATUSES = {
        'pending': 'Pending',
        'approved': 'Approved',
        'denied': 'Denied'
    }
    
    def __repr__(self):
        return f'<TimeOff {self.employee.full_name}: {self.start_date} to {self.end_date}>'
    
    def get_request_type_display(self):
        """Get human-readable request type"""
        return self.REQUEST_TYPES.get(self.request_type, self.request_type.title())
    
    def get_status_display(self):
        """Get human-readable status"""
        return self.STATUSES.get(self.status, self.status.title())
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'employee_name': self.employee.full_name,
            'request_type': self.request_type,
            'request_type_display': self.get_request_type_display(),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'days_requested': self.days_requested,
            'reason': self.reason,
            'status': self.status,
            'status_display': self.get_status_display(),
            'created_at': self.created_at.isoformat()
        }