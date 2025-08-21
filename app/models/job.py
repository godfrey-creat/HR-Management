"""
Job and application models for recruitment
"""

from datetime import datetime
from app import db

class Job(db.Model):
    """Job posting model for recruitment"""
    
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Job Information
    title = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100))
    employment_type = db.Column(db.String(20), default='full_time')  # full_time, part_time, contract, internship
    experience_level = db.Column(db.String(20), default='mid_level')  # entry, mid_level, senior, executive
    
    # Job Details
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    responsibilities = db.Column(db.Text)
    benefits = db.Column(db.Text)
    
    # Compensation
    salary_min = db.Column(db.Numeric(10, 2))
    salary_max = db.Column(db.Numeric(10, 2))
    salary_currency = db.Column(db.String(3), default='USD')
    
    # Job Status and Dates
    status = db.Column(db.String(20), default='draft')  # draft, published, closed, filled
    published_date = db.Column(db.DateTime)
    closing_date = db.Column(db.Date)
    filled_date = db.Column(db.DateTime)
    
    # Hiring Information
    positions_available = db.Column(db.Integer, default=1)
    hiring_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    hiring_manager = db.relationship('User', foreign_keys=[hiring_manager_id])
    
    # System fields
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('JobApplication', backref='job', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constants
    EMPLOYMENT_TYPES = {
        'full_time': 'Full Time',
        'part_time': 'Part Time',
        'contract': 'Contract',
        'internship': 'Internship'
    }
    
    EXPERIENCE_LEVELS = {
        'entry': 'Entry Level',
        'mid_level': 'Mid Level',
        'senior': 'Senior Level',
        'executive': 'Executive'
    }
    
    STATUSES = {
        'draft': 'Draft',
        'published': 'Published',
        'closed': 'Closed',
        'filled': 'Filled'
    }
    
    def __repr__(self):
        return f'<Job {self.job_id}: {self.title}>'
    
    def get_employment_type_display(self):
        """Get human-readable employment type"""
        return self.EMPLOYMENT_TYPES.get(self.employment_type, self.employment_type.title())
    
    def get_experience_level_display(self):
        """Get human-readable experience level"""
        return self.EXPERIENCE_LEVELS.get(self.experience_level, self.experience_level.title())
    
    def get_status_display(self):
        """Get human-readable status"""
        return self.STATUSES.get(self.status, self.status.title())
    
    def get_salary_range(self):
        """Get formatted salary range"""
        if self.salary_min and self.salary_max:
            return f"{self.salary_currency} {self.salary_min:,.0f} - {self.salary_max:,.0f}"
        elif self.salary_min:
            return f"{self.salary_currency} {self.salary_min:,.0f}+"
        return "Salary not specified"
    
    def get_applications_count(self):
        """Get total number of applications"""
        return self.applications.count()
    
    def get_new_applications_count(self):
        """Get number of new applications"""
        return self.applications.filter_by(status='applied').count()
    
    def is_active(self):
        """Check if job is actively accepting applications"""
        return self.status == 'published' and (not self.closing_date or self.closing_date >= datetime.utcnow().date())
    
    def days_since_posted(self):
        """Get number of days since job was posted"""
        if self.published_date:
            return (datetime.utcnow() - self.published_date).days
        return 0
    
    def to_dict(self):
        """Convert job to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'title': self.title,
            'department': self.department,
            'location': self.location,
            'employment_type': self.employment_type,
            'employment_type_display': self.get_employment_type_display(),
            'experience_level': self.experience_level,
            'experience_level_display': self.get_experience_level_display(),
            'description': self.description,
            'requirements': self.requirements,
            'salary_range': self.get_salary_range(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'closing_date': self.closing_date.isoformat() if self.closing_date else None,
            'positions_available': self.positions_available,
            'applications_count': self.get_applications_count(),
            'new_applications_count': self.get_new_applications_count(),
            'is_active': self.is_active(),
            'days_since_posted': self.days_since_posted(),
            'created_at': self.created_at.isoformat()
        }

class JobApplication(db.Model):
    """Job application model"""
    
    __tablename__ = 'job_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Job and Applicant
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    
    # Applicant Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    
    # Application Details
    cover_letter = db.Column(db.Text)
    resume_path = db.Column(db.String(200))
    portfolio_url = db.Column(db.String(200))
    linkedin_url = db.Column(db.String(200))
    
    # Experience and Qualifications
    years_experience = db.Column(db.Integer)
    current_salary = db.Column(db.Numeric(10, 2))
    expected_salary = db.Column(db.Numeric(10, 2))
    availability_date = db.Column(db.Date)
    # Application Status and Process
    status = db.Column(db.String(20), default='applied')  # applied, screening, interviewed, offered, hired, rejected
    source = db.Column(db.String(50))  # website, referral, job_board, social_media
    
    # Interview and Feedback
    interview_date = db.Column(db.DateTime)
    interviewer_notes = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5 rating
    
    # Assignment and Review
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    reviewed_at = db.Column(db.DateTime)
    
    # Timestamps
    applied_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constants
    STATUSES = {
        'applied': 'Applied',
        'screening': 'Screening',
        'interviewed': 'Interviewed',
        'offered': 'Offered',
        'hired': 'Hired',
        'rejected': 'Rejected'
    }
    
    SOURCES = {
        'website': 'Company Website',
        'referral': 'Employee Referral',
        'job_board': 'Job Board',
        'social_media': 'Social Media',
        'recruiter': 'Recruiter'
    }
    
    def __repr__(self):
        return f'<JobApplication {self.application_id}: {self.full_name}>'
    
    @property
    def full_name(self):
        """Get applicant's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_status_display(self):
        """Get human-readable status"""
        return self.STATUSES.get(self.status, self.status.title())
    
    def get_source_display(self):
        """Get human-readable source"""
        return self.SOURCES.get(self.source, self.source.title() if self.source else 'Unknown')
    
    def days_since_applied(self):
        """Get number of days since application was submitted"""
        return (datetime.utcnow() - self.applied_at).days
    
    def get_salary_expectation(self):
        """Get formatted salary expectation"""
        if self.expected_salary:
            return f"${self.expected_salary:,.0f}"
        return "Not specified"
    
    def to_dict(self):
        """Convert application to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'job_title': self.job.title,
            'job_id': self.job.job_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'years_experience': self.years_experience,
            'expected_salary': float(self.expected_salary) if self.expected_salary else None,
            'salary_expectation': self.get_salary_expectation(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'source': self.source,
            'source_display': self.get_source_display(),
            'rating': self.rating,
            'days_since_applied': self.days_since_applied(),
            'applied_at': self.applied_at.isoformat(),
            'interview_date': self.interview_date.isoformat() if self.interview_date else None
        }