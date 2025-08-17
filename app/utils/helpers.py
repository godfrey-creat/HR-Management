# ============================================================================
# File: app/utils/helpers.py
# Helper Functions
# ============================================================================

from datetime import datetime, timedelta
import re
import uuid
import os
from werkzeug.utils import secure_filename

def generate_employee_id():
    """Generate unique employee ID"""
    return f"EMP{str(uuid.uuid4())[:8].upper()}"

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def calculate_working_days(start_date, end_date):
    """Calculate working days between two dates (excluding weekends)"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    working_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            working_days += 1
        current_date += timedelta(days=1)
    
    return working_days

def calculate_overtime(clock_in, clock_out, regular_hours=8):
    """Calculate overtime hours"""
    if not clock_in or not clock_out:
        return 0
    
    total_minutes = (clock_out - clock_in).total_seconds() / 60
    total_hours = total_minutes / 60
    
    return max(0, total_hours - regular_hours)

def allowed_file(filename, allowed_extensions={'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, upload_folder='uploads'):
    """Save uploaded file securely"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return filepath
    return None