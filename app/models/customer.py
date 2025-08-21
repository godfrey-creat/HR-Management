"""
Customer model for CRM management
"""

from datetime import datetime
from app import db

class Customer(db.Model):
    """Customer model for CRM management"""
    
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Company Information
    company_name = db.Column(db.String(100))
    industry = db.Column(db.String(50))
    company_size = db.Column(db.String(20))  # startup, small, medium, large, enterprise
    website = db.Column(db.String(200))
    
    # Primary Contact Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    job_title = db.Column(db.String(100))
    
    # Address Information
    address_line1 = db.Column(db.String(100))
    address_line2 = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(50))
    
    # Customer Status and Classification
    status = db.Column(db.String(20), default='active')  # active, inactive, prospect, lost
    customer_type = db.Column(db.String(20), default='prospect')  # prospect, customer, partner
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    
    # Business Information
    annual_revenue = db.Column(db.Numeric(15, 2))
    customer_since = db.Column(db.Date)
    last_contact_date = db.Column(db.Date)
    next_contact_date = db.Column(db.Date)
    
    # Sales Information
    total_value = db.Column(db.Numeric(15, 2), default=0)
    lifetime_value = db.Column(db.Numeric(15, 2), default=0)
    
    # Social Media and Communication
    linkedin_url = db.Column(db.String(200))
    twitter_handle = db.Column(db.String(50))
    preferred_contact_method = db.Column(db.String(20), default='email')  # email, phone, social
    
    # Notes and Tags
    notes = db.Column(db.Text)
    tags = db.Column(db.String(500))  # Comma-separated tags
    
    # Assignment and Territory
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_user = db.relationship('User', foreign_keys=[assigned_to])
    territory = db.Column(db.String(50))
    
    # System fields
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    leads = db.relationship('Lead', backref='customer', lazy='dynamic')
    tickets = db.relationship('Ticket', backref='customer', lazy='dynamic')
    
    # Constants
    STATUSES = {
        'active': 'Active',
        'inactive': 'Inactive',
        'prospect': 'Prospect',
        'lost': 'Lost Customer'
    }
    
    CUSTOMER_TYPES = {
        'prospect': 'Prospect',
        'customer': 'Customer',
        'partner': 'Partner'
    }
    
    PRIORITIES = {
        'low': 'Low',
        'medium': 'Medium',
        'high': 'High'
    }
    
    COMPANY_SIZES = {
        'startup': 'Startup (1-10)',
        'small': 'Small (11-50)',
        'medium': 'Medium (51-200)',
        'large': 'Large (201-1000)',
        'enterprise': 'Enterprise (1000+)'
    }
    
    def __repr__(self):
        return f'<Customer {self.customer_id}: {self.company_name or self.full_name}>'
    
    @property
    def full_name(self):
        """Get customer's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self):
        """Get display name (company or full name)"""
        return self.company_name or self.full_name
    
    @property
    def full_address(self):
        """Get formatted full address"""
        parts = [self.address_line1, self.address_line2, self.city, self.state, self.postal_code, self.country]
        return ', '.join([part for part in parts if part])
    
    def get_status_display(self):
        """Get human-readable status"""
        return self.STATUSES.get(self.status, self.status.title())
    
    def get_customer_type_display(self):
        """Get human-readable customer type"""
        return self.CUSTOMER_TYPES.get(self.customer_type, self.customer_type.title())
    
    def get_priority_display(self):
        """Get human-readable priority"""
        return self.PRIORITIES.get(self.priority, self.priority.title())
    
    def get_company_size_display(self):
        """Get human-readable company size"""
        return self.COMPANY_SIZES.get(self.company_size, self.company_size.title())
    
    def get_assigned_user_name(self):
        """Get assigned user's full name"""
        if self.assigned_user:
            return self.assigned_user.full_name
        return None
    
    def get_tags_list(self):
        """Get tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def add_tag(self, tag):
        """Add a tag to the customer"""
        current_tags = self.get_tags_list()
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = ', '.join(current_tags)
    
    def remove_tag(self, tag):
        """Remove a tag from the customer"""
        current_tags = self.get_tags_list()
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = ', '.join(current_tags)
    
    def get_open_tickets_count(self):
        """Get count of open support tickets"""
        return self.tickets.filter_by(status='open').count()
    
    def get_active_leads_count(self):
        """Get count of active leads"""
        return self.leads.filter(Lead.status.in_(['new', 'qualified', 'proposal'])).count()
    
    def to_dict(self):
        """Convert customer to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'company_name': self.company_name,
            'industry': self.industry,
            'company_size': self.company_size,
            'company_size_display': self.get_company_size_display(),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'email': self.email,
            'phone': self.phone,
            'job_title': self.job_title,
            'full_address': self.full_address,
            'status': self.status,
            'status_display': self.get_status_display(),
            'customer_type': self.customer_type,
            'customer_type_display': self.get_customer_type_display(),
            'priority': self.priority,
            'priority_display': self.get_priority_display(),
            'total_value': float(self.total_value) if self.total_value else 0,
            'lifetime_value': float(self.lifetime_value) if self.lifetime_value else 0,
            'assigned_user_name': self.get_assigned_user_name(),
            'tags': self.get_tags_list(),
            'open_tickets_count': self.get_open_tickets_count(),
            'active_leads_count': self.get_active_leads_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None
        }