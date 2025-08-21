"""
Support ticket model for customer service
"""

from datetime import datetime
from app import db

class Ticket(db.Model):
    """Support ticket model for customer service management"""
    
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Ticket Information
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Customer Information
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20))
    
    # Ticket Classification
    category = db.Column(db.String(50))  # technical, billing, general, feature_request
    subcategory = db.Column(db.String(50))
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    severity = db.Column(db.String(20), default='minor')  # minor, major, critical, blocker
    
    # Ticket Status and Resolution
    status = db.Column(db.String(20), default='open')  # open, in_progress, waiting, resolved, closed
    resolution = db.Column(db.Text)
    resolution_date = db.Column(db.DateTime)
    
    # Assignment and Escalation
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    escalated_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    escalation_reason = db.Column(db.Text)
    escalation_date = db.Column(db.DateTime)
    
    # SLA and Timing
    sla_breach = db.Column(db.Boolean, default=False)
    first_response_time = db.Column(db.DateTime)
    resolution_time = db.Column(db.DateTime)
    
    # Communication Channel
    channel = db.Column(db.String(20), default='email')  # email, phone, chat, portal, social
    
    # Customer Satisfaction
    satisfaction_rating = db.Column(db.Integer)  # 1-5 rating
    satisfaction_feedback = db.Column(db.Text)
    
    # Tags and Notes
    tags = db.Column(db.String(500))  # Comma-separated tags
    internal_notes = db.Column(db.Text)
    
    # System fields
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    responses = db.relationship('TicketResponse', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constants
    CATEGORIES = {
        'technical': 'Technical Support',
        'billing': 'Billing/Account',
        'general': 'General Inquiry',
        'feature_request': 'Feature Request',
        'bug_report': 'Bug Report',
        'training': 'Training/How-to'
    }
    
    PRIORITIES = {
        'low': 'Low',
        'medium': 'Medium',
        'high': 'High',
        'urgent': 'Urgent'
    }
    
    SEVERITIES = {
        'minor': 'Minor',
        'major': 'Major',
        'critical': 'Critical',
        'blocker': 'System Down'
    }
    
    STATUSES = {
        'open': 'Open',
        'in_progress': 'In Progress',
        'waiting': 'Waiting for Customer',
        'resolved': 'Resolved',
        'closed': 'Closed'
    }
    
    CHANNELS = {
        'email': 'Email',
        'phone': 'Phone',
        'chat': 'Live Chat',
        'portal': 'Customer Portal',
        'social': 'Social Media'
    }
    
    def __repr__(self):
        return f'<Ticket {self.ticket_id}: {self.subject}>'
    
    def get_category_display(self):
        """Get human-readable category"""
        return self.CATEGORIES.get(self.category, self.category.title() if self.category else 'General')
    
    def get_priority_display(self):
        """Get human-readable priority"""
        return self.PRIORITIES.get(self.priority, self.priority.title())
    
    def get_severity_display(self):
        """Get human-readable severity"""
        return self.SEVERITIES.get(self.severity, self.severity.title())
    
    def get_status_display(self):
        """Get human-readable status"""
        return self.STATUSES.get(self.status, self.status.title())
    
    def get_channel_display(self):
        """Get human-readable channel"""
        return self.CHANNELS.get(self.channel, self.channel.title())
    
    def get_assigned_user_name(self):
        """Get assigned user's full name"""
        if self.assigned_to:
            from app.models.user import User
            user = User.query.get(self.assigned_to)
            return user.full_name if user else None
        return None
    
    def get_customer_display_name(self):
        """Get customer display name"""
        return self.customer.display_name if self.customer else self.customer_name
    
    def get_tags_list(self):
        """Get tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def is_overdue(self):
        """Check if ticket is overdue based on priority SLA"""
        if self.status in ['resolved', 'closed']:
            return False
        
        hours_since_created = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        
        sla_hours = {
            'urgent': 4,
            'high': 24,
            'medium': 48,
            'low': 72
        }
        
        return hours_since_created > sla_hours.get(self.priority, 48)
    
    def time_to_first_response(self):
        """Calculate time to first response in hours"""
        if self.first_response_time:
            return (self.first_response_time - self.created_at).total_seconds() / 3600
        return None
    
    def time_to_resolution(self):
        """Calculate time to resolution in hours"""
        if self.resolution_time:
            return (self.resolution_time - self.created_at).total_seconds() / 3600
        return None
    
    def get_response_count(self):
        """Get number of responses to this ticket"""
        return self.responses.count()
    
    def get_last_response(self):
        """Get the most recent response"""
        return self.responses.order_by(TicketResponse.created_at.desc()).first()
    
    def age_in_days(self):
        """Get ticket age in days"""
        return (datetime.utcnow() - self.created_at).days
    
    def mark_resolved(self, resolution_text, resolved_by):
        """Mark ticket as resolved"""
        self.status = 'resolved'
        self.resolution = resolution_text
        self.resolution_date = datetime.utcnow()
        self.resolution_time = datetime.utcnow()
        
        # Add resolution response
        response = TicketResponse(
            ticket_id=self.id,
            response_type='resolution',
            message=resolution_text,
            is_internal=False,
            created_by=resolved_by
        )
        db.session.add(response)
    
    def to_dict(self):
        """Convert ticket to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'subject': self.subject,
            'description': self.description,
            'customer_name': self.get_customer_display_name(),
            'customer_email': self.customer_email,
            'category': self.category,
            'category_display': self.get_category_display(),
            'priority': self.priority,
            'priority_display': self.get_priority_display(),
            'severity': self.severity,
            'severity_display': self.get_severity_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'channel': self.channel,
            'channel_display': self.get_channel_display(),
            'assigned_user_name': self.get_assigned_user_name(),
            'tags': self.get_tags_list(),
            'is_overdue': self.is_overdue(),
            'age_in_days': self.age_in_days(),
            'response_count': self.get_response_count(),
            'satisfaction_rating': self.satisfaction_rating,
            'created_at': self.created_at.isoformat(),
            'resolution_date': self.resolution_date.isoformat() if self.resolution_date else None,
            'time_to_resolution': self.time_to_resolution()
        }

class TicketResponse(db.Model):
    """Ticket response/communication model"""
    
    __tablename__ = 'ticket_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    
    # Response Information
    response_type = db.Column(db.String(20), default='reply')  # reply, note, resolution, escalation
    message = db.Column(db.Text, nullable=False)
    
    # Response Properties
    is_internal = db.Column(db.Boolean, default=False)  # Internal note or customer-visible
    email_sent = db.Column(db.Boolean, default=False)  # Was email notification sent
    
    # Attachments
    attachments = db.Column(db.String(500))  # JSON array of file paths
    
    # System fields
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    author = db.relationship('User', backref='ticket_responses')
    
    RESPONSE_TYPES = {
        'reply': 'Reply',
        'note': 'Internal Note',
        'resolution': 'Resolution',
        'escalation': 'Escalation'
    }
    
    def __repr__(self):
        return f'<TicketResponse {self.ticket.ticket_id} - {self.response_type}>'
    
    def get_response_type_display(self):
        """Get human-readable response type"""
        return self.RESPONSE_TYPES.get(self.response_type, self.response_type.title())
    
    def get_author_name(self):
        """Get author's full name"""
        return self.author.full_name if self.author else 'System'
    
    def to_dict(self):
        """Convert response to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'response_type': self.response_type,
            'response_type_display': self.get_response_type_display(),
            'message': self.message,
            'is_internal': self.is_internal,
            'author_name': self.get_author_name(),
            'created_at': self.created_at.isoformat()
        }