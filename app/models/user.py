"""
User model for authentication and authorization
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # User profile
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(100))
    
    # System fields
    role = db.Column(db.String(20), nullable=False, default='employee')
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    employees = db.relationship('Employee', backref='created_by_user', lazy='dynamic', foreign_keys='Employee.created_by')
    customers = db.relationship('Customer', backref='created_by_user', lazy='dynamic', foreign_keys='Customer.created_by')
    
    # ✅ Disambiguated job relationships
    jobs_posted = db.relationship(
        'Job',
        foreign_keys='Job.posted_by',
        backref='poster',
        lazy='dynamic'
    )
    jobs_managed = db.relationship(
        'Job',
        foreign_keys='Job.hiring_manager_id',
        backref='manager',
        lazy='dynamic'
    )

    leads = db.relationship('Lead', backref='assigned_to_user', lazy='dynamic', foreign_keys='Lead.assigned_to')
    tickets = db.relationship('Ticket', backref='assigned_to_user', lazy='dynamic', foreign_keys='Ticket.assigned_to')
    
    # Role constants
    ROLES = {
        'admin': 'Administrator',
        'hr_manager': 'HR Manager',
        'sales_manager': 'Sales Manager',
        'support_agent': 'Support Agent',
        'employee': 'Employee',
        'customer': 'Customer'
    }
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            self.role = 'employee'
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_role_display(self):
        """Get human-readable role name"""
        return self.ROLES.get(self.role, self.role.title())
    
    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role
    
    def has_any_role(self, *roles):
        """Check if user has any of the specified roles"""
        return self.role in roles
    
    def can_access_hr(self):
        """Check if user can access HR module"""
        return self.has_any_role('admin', 'hr_manager')
    
    def can_access_crm(self):
        """Check if user can access CRM module"""
        return self.has_any_role('admin', 'sales_manager', 'support_agent')
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.has_role('admin')
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'role_display': self.get_role_display(),
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
