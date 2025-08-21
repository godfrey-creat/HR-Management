"""
Helper functions for People360
"""

import random
import string
from datetime import datetime, date
from flask import url_for

def generate_id(prefix='', length=8):
    """Generate a unique ID with optional prefix"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length))
    return f"{prefix}{random_part}" if prefix else random_part

def generate_employee_id():
    """Generate unique employee ID"""
    return generate_id('EMP', 6)

def generate_customer_id():
    """Generate unique customer ID"""
    return generate_id('CUS', 6)

def generate_job_id():
    """Generate unique job ID"""
    return generate_id('JOB', 6)

def generate_lead_id():
    """Generate unique lead ID"""
    return generate_id('LED', 6)

def generate_ticket_id():
    """Generate unique ticket ID"""
    return generate_id('TKT', 6)

def generate_application_id():
    """Generate unique application ID"""
    return generate_id('APP', 6)

def format_currency(amount, currency='USD'):
    """Format currency amount"""
    if amount is None:
        return 'N/A'
    
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'KES': 'KSh'
    }
    
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"

def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_avatar_url(user, size=50):
    """Get avatar URL for user (placeholder implementation)"""
    if user.avatar:
        return url_for('static', filename=f'avatars/{user.avatar}')
    
    # Default avatar based on initials
    initials = ''
    if user.first_name and user.last_name:
        initials = f"{user.first_name[0]}{user.last_name[0]}".upper()
    elif user.username:
        initials = user.username[:2].upper()
    
    # For now, return a placeholder URL - in production you might use a service like Gravatar
    return f"https://ui-avatars.com/api/?name={initials}&size={size}&background=007bff&color=white"

def format_phone(phone):
    """Format phone number"""
    if not phone:
        return None
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if can't format

def truncate_text(text, length=100, suffix='...'):
    """Truncate text to specified length"""
    if not text or len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + suffix

def get_priority_class(priority):
    """Get CSS class for priority level"""
    priority_classes = {
        'low': 'success',
        'medium': 'warning',
        'high': 'danger',
        'urgent': 'danger'
    }
    return priority_classes.get(priority, 'secondary')

def get_status_class(status, status_type='default'):
    """Get CSS class for various status types"""
    if status_type == 'ticket':
        status_classes = {
            'open': 'primary',
            'in_progress': 'warning',
            'waiting': 'info',
            'resolved': 'success',
            'closed': 'secondary'
        }
    elif status_type == 'lead':
        status_classes = {
            'new': 'primary',
            'qualified': 'info',
            'proposal': 'warning',
            'negotiation': 'warning',
            'won': 'success',
            'lost': 'danger'
        }
    elif status_type == 'employee':
        status_classes = {
            'active': 'success',
            'inactive': 'warning',
            'terminated': 'danger',
            'on_leave': 'info'
        }
    else:
        status_classes = {
            'active': 'success',
            'inactive': 'secondary',
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }
    
    return status_classes.get(status, 'secondary')

def paginate_query(query, page, per_page=10):
    """Paginate a SQLAlchemy query"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def safe_int(value, default=0):
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def format_datetime(dt, format='%Y-%m-%d %H:%M'):
    """Format datetime for display"""
    if not dt:
        return 'N/A'
    return dt.strftime(format)

def time_ago(dt):
    """Get human-readable time ago string"""
    if not dt:
        return 'Never'
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"