"""
Lead model for CRM sales pipeline
"""

from datetime import datetime
from app import db

class Lead(db.Model):
    """Lead model for sales pipeline management"""
    
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Lead Information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Customer/Prospect Information
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    company_name = db.Column(db.String(100))
    contact_name = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20))
    
    # Lead Classification
    source = db.Column(db.String(50))  # website, referral, cold_call, email, social_media, event
    lead_type = db.Column(db.String(20), default='prospect')  # prospect, existing_customer, partner
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    
    # Sales Information
    estimated_value = db.Column(db.Numeric(15, 2))
    probability = db.Column(db.Integer, default=0)  # 0-100%
    expected_close_date = db.Column(db.Date)
    actual_close_date = db.Column(db.Date)
    
    # Pipeline Status
    status = db.Column(db.String(20), default='new')  # new, qualified, proposal, negotiation, won, lost
    stage = db.Column(db.String(50), default='Initial Contact')
    
    # Assignment and Territory
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    territory = db.Column(db.String(50))
    
    # Follow-up and Activity
    last_activity_date = db.Column(db.Date)
    next_activity_date = db.Column(db.Date)
    next_activity_type = db.Column(db.String(50))  # call, email, meeting, proposal
    
    # Qualification Information
    budget = db.Column(db.Numeric(15, 2))
    decision_maker = db.Column(db.String(100))
    timeline = db.Column(db.String(100))
    pain_points = db.Column(db.Text)
    solution_fit = db.Column(db.Text)
    
    # Competition and Context
    competitors = db.Column(db.String(500))  # Comma-separated list
    lost_reason = db.Column(db.String(200))
    
    # Notes and Tags
    notes = db.Column(db.Text)
    tags = db.Column(db.String(500))  # Comma-separated tags
    
    # System fields
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = db.relationship('LeadActivity', backref='lead', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constants
    SOURCES = {
        'website': 'Website',
        'referral': 'Referral',
        'cold_call': 'Cold Call',
        'email': 'Email Campaign',
        'social_media': 'Social Media',
        'event': 'Event/Trade Show',
        'advertisement': 'Advertisement',
        'partner': 'Partner'
    }
    
    LEAD_TYPES = {
        'prospect': 'New Prospect',
        'existing_customer': 'Existing Customer',
        'partner': 'Partner'
    }
    
    PRIORITIES = {
        'low': 'Low',
        'medium': 'Medium',
        'high': 'High',
        'urgent': 'Urgent'
    }
    
    STATUSES = {
        'new': 'New',
        'qualified': 'Qualified',
        'proposal': 'Proposal Sent',
        'negotiation': 'In Negotiation',
        'won': 'Won',
        'lost': 'Lost'
    }
    
    STAGES = [
        'Initial Contact',
        'Qualification',
        'Needs Analysis',
        'Proposal',
        'Negotiation',
        'Closed Won',
        'Closed Lost'
    ]
    
    ACTIVITY_TYPES = {
        'call': 'Phone Call',
        'email': 'Email',
        'meeting': 'Meeting',
        'proposal': 'Send Proposal',
        'demo': 'Product Demo',
        'follow_up': 'Follow Up'
    }
    
    def __repr__(self):
        return f'<Lead {self.lead_id}: {self.title}>'
    
    def get_source_display(self):
        """Get human-readable source"""
        return self.SOURCES.get(self.source, self.source.title() if self.source else 'Unknown')
    
    def get_lead_type_display(self):
        """Get human-readable lead type"""
        return self.LEAD_TYPES.get(self.lead_type, self.lead_type.title())
    
    def get_priority_display(self):
        """Get human-readable priority"""
        return self.PRIORITIES.get(self.priority, self.priority.title())
    
    def get_status_display(self):
        """Get human-readable status"""
        return self.STATUSES.get(self.status, self.status.title())
    
    def get_assigned_user_name(self):
        """Get assigned user's full name"""
        if self.assigned_to:
            from app.models.user import User
            user = User.query.get(self.assigned_to)
            return user.full_name if user else None
        return None
    
    def get_customer_name(self):
        """Get customer name if linked"""
        return self.customer.display_name if self.customer else self.company_name
    
    def get_tags_list(self):
        """Get tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def get_competitors_list(self):
        """Get competitors as a list"""
        if self.competitors:
            return [comp.strip() for comp in self.competitors.split(',') if comp.strip()]
        return []
    
    def is_overdue(self):
        """Check if lead is overdue for follow-up"""
        if self.next_activity_date:
            return self.next_activity_date < datetime.utcnow().date()
        return False
    
    def days_in_pipeline(self):
        """Calculate days in sales pipeline"""
        return (datetime.utcnow() - self.created_at).days
    
    def get_weighted_value(self):
        """Get probability-weighted lead value"""
        if self.estimated_value and self.probability:
            return float(self.estimated_value) * (self.probability / 100.0)
        return 0
    
    def get_recent_activities(self, limit=5):
        """Get recent activities for this lead"""
        return self.activities.order_by(LeadActivity.created_at.desc()).limit(limit).all()
    
    def to_dict(self):
        """Convert lead to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'title': self.title,
            'description': self.description,
            'customer_name': self.get_customer_name(),
            'contact_name': self.contact_name,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'source': self.source,
            'source_display': self.get_source_display(),
            'priority': self.priority,
            'priority_display': self.get_priority_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'stage': self.stage,
            'estimated_value': float(self.estimated_value) if self.estimated_value else 0,
            'probability': self.probability,
            'weighted_value': self.get_weighted_value(),
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
            'assigned_user_name': self.get_assigned_user_name(),
            'tags': self.get_tags_list(),
            'is_overdue': self.is_overdue(),
            'days_in_pipeline': self.days_in_pipeline(),
            'created_at': self.created_at.isoformat(),
            'next_activity_date': self.next_activity_date.isoformat() if self.next_activity_date else None,
            'next_activity_type': self.next_activity_type
        }

class LeadActivity(db.Model):
    """Activity tracking for leads"""
    
    __tablename__ = 'lead_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    
    # Activity Information
    activity_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Activity Details
    activity_date = db.Column(db.DateTime, default=datetime.utcnow)
    duration_minutes = db.Column(db.Integer)
    outcome = db.Column(db.String(50))  # successful, unsuccessful, follow_up_needed
    
    # Follow-up
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date)
    follow_up_notes = db.Column(db.Text)
    
    # System fields
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    OUTCOMES = {
        'successful': 'Successful',
        'unsuccessful': 'Unsuccessful',
        'follow_up_needed': 'Follow-up Needed',
        'no_answer': 'No Answer',
        'voicemail': 'Left Voicemail'
    }
    
    def __repr__(self):
        return f'<LeadActivity {self.subject} - {self.lead.lead_id}>'
    
    def get_outcome_display(self):
        """Get human-readable outcome"""
        return self.OUTCOMES.get(self.outcome, self.outcome.title() if self.outcome else 'Unknown')
    
    def get_activity_type_display(self):
        """Get human-readable activity type"""
        return Lead.ACTIVITY_TYPES.get(self.activity_type, self.activity_type.title())
    
    def to_dict(self):
        """Convert activity to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'activity_type': self.activity_type,
            'activity_type_display': self.get_activity_type_display(),
            'subject': self.subject,
            'description': self.description,
            'activity_date': self.activity_date.isoformat(),
            'duration_minutes': self.duration_minutes,
            'outcome': self.outcome,
            'outcome_display': self.get_outcome_display(),
            'follow_up_required': self.follow_up_required,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'created_at': self.created_at.isoformat()
        }