"""
API routes for People360
RESTful API endpoints for mobile apps and integrations
"""

from flask import Blueprint, jsonify, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import User, Employee, Customer, Job, Lead, Ticket
from app.utils.helpers import safe_int

bp = Blueprint('api', __name__)

# Error handlers
@bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Access forbidden'}), 403

@bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Helper functions
def paginate_api_query(query, page=1, per_page=20):
    """Paginate query for API responses"""
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'has_prev': page > 1,
        'has_next': page * per_page < total
    }

# Authentication endpoints
@bp.route('/auth/me')
@login_required
def current_user_info():
    """Get current user information"""
    return jsonify(current_user.to_dict())

# Employee API endpoints
@bp.route('/employees')
@login_required
def get_employees():
    """Get list of employees"""
    if not current_user.can_access_hr():
        abort(403)
    
    page = safe_int(request.args.get('page', 1), 1)
    per_page = min(safe_int(request.args.get('per_page', 20), 20), 100)
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    status = request.args.get('status', '').strip()
    
    query = Employee.query
    
    # Apply filters
    if search:
        query = query.filter(
            (Employee.first_name.contains(search)) |
            (Employee.last_name.contains(search)) |
            (Employee.email.contains(search)) |
            (Employee.employee_id.contains(search))
        )
    
    if department:
        query = query.filter_by(department=department)
    
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(Employee.created_at.desc())
    
    # Paginate
    result = paginate_api_query(query, page, per_page)
    result['items'] = [emp.to_dict() for emp in result['items']]
    
    return jsonify(result)

@bp.route('/employees/<int:id>')
@login_required
def get_employee(id):
    """Get specific employee"""
    if not current_user.can_access_hr():
        abort(403)
    
    employee = Employee.query.get_or_404(id)
    return jsonify(employee.to_dict())

@bp.route('/employees', methods=['POST'])
@login_required
def create_employee():
    """Create new employee"""
    if not current_user.can_access_hr():
        abort(403)
    
    data = request.get_json()
    if not data:
        abort(400)
    
    # Validate required fields
    required_fields = ['first_name', 'last_name', 'email', 'position']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Generate employee ID
    from app.utils.helpers import generate_employee_id
    employee_id = generate_employee_id()
    while Employee.query.filter_by(employee_id=employee_id).first():
        employee_id = generate_employee_id()
    
    try:
        employee = Employee(
            employee_id=employee_id,
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data.get('phone'),
            department=data.get('department'),
            position=data['position'],
            hire_date=datetime.strptime(data.get('hire_date', datetime.utcnow().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
            employment_type=data.get('employment_type', 'full_time'),
            salary=data.get('salary'),
            created_by=current_user.id
        )
        
        db.session.add(employee)
        db.session.commit()
        
        return jsonify(employee.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/employees/<int:id>', methods=['PUT'])
@login_required
def update_employee(id):
    """Update employee information"""
    if not current_user.can_access_hr():
        abort(403)
    
    employee = Employee.query.get_or_404(id)
    data = request.get_json()
    if not data:
        abort(400)
    
    try:
        # Update fields if provided
        updatable_fields = ['first_name', 'last_name', 'email', 'phone', 'department', 
                           'position', 'employment_type', 'salary', 'status']
        
        for field in updatable_fields:
            if field in data:
                setattr(employee, field, data[field])
        
        # Handle date fields specially
        if 'hire_date' in data:
            employee.hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date()
        
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(employee.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/employees/<int:id>', methods=['DELETE'])
@login_required
def delete_employee(id):
    """Delete employee"""
    if not current_user.can_access_hr():
        abort(403)
    
    employee = Employee.query.get_or_404(id)
    
    try:
        db.session.delete(employee)
        db.session.commit()
        return jsonify({'message': 'Employee deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Customer API endpoints
@bp.route('/customers')
@login_required
def get_customers():
    """Get list of customers"""
    if not current_user.can_access_crm():
        abort(403)
    
    page = safe_int(request.args.get('page', 1), 1)
    per_page = min(safe_int(request.args.get('per_page', 20), 20), 100)
    search = request.args.get('search', '').strip()
    customer_type = request.args.get('customer_type', '').strip()
    
    query = Customer.query
    
    # Apply filters
    if search:
        query = query.filter(
            (Customer.first_name.contains(search)) |
            (Customer.last_name.contains(search)) |
            (Customer.company_name.contains(search)) |
            (Customer.email.contains(search)) |
            (Customer.customer_id.contains(search))
        )
    
    if customer_type:
        query = query.filter_by(customer_type=customer_type)
    
    query = query.order_by(Customer.created_at.desc())
    
    # Paginate
    result = paginate_api_query(query, page, per_page)
    result['items'] = [customer.to_dict() for customer in result['items']]
    
    return jsonify(result)

@bp.route('/customers/<int:id>')
@login_required
def get_customer(id):
    """Get specific customer"""
    if not current_user.can_access_crm():
        abort(403)
    
    customer = Customer.query.get_or_404(id)
    return jsonify(customer.to_dict())

@bp.route('/customers', methods=['POST'])
@login_required
def create_customer():
    """Create new customer"""
    if not current_user.can_access_crm():
        abort(403)
    
    data = request.get_json()
    if not data:
        abort(400)
    
    # Validate required fields
    required_fields = ['first_name', 'last_name', 'email']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Generate customer ID
    from app.utils.helpers import generate_customer_id
    customer_id = generate_customer_id()
    while Customer.query.filter_by(customer_id=customer_id).first():
        customer_id = generate_customer_id()
    
    try:
        customer = Customer(
            customer_id=customer_id,
            company_name=data.get('company_name'),
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data.get('phone'),
            job_title=data.get('job_title'),
            industry=data.get('industry'),
            customer_type=data.get('customer_type', 'prospect'),
            priority=data.get('priority', 'medium'),
            assigned_to=current_user.id,
            created_by=current_user.id
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify(customer.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/customers/<int:id>', methods=['PUT'])
@login_required
def update_customer(id):
    """Update customer information"""
    if not current_user.can_access_crm():
        abort(403)
    
    customer = Customer.query.get_or_404(id)
    data = request.get_json()
    if not data:
        abort(400)
    
    try:
        updatable_fields = ['company_name', 'first_name', 'last_name', 'email', 'phone',
                           'job_title', 'industry', 'customer_type', 'priority', 'assigned_to']
        
        for field in updatable_fields:
            if field in data:
                setattr(customer, field, data[field])
        
        customer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(customer.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/customers/<int:id>', methods=['DELETE'])
@login_required
def delete_customer(id):
    """Delete customer"""
    if not current_user.can_access_crm():
        abort(403)
    
    customer = Customer.query.get_or_404(id)
    
    try:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'message': 'Customer deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Lead API endpoints
@bp.route('/leads')
@login_required
def get_leads():
    """Get list of leads"""
    if not current_user.can_access_crm():
        abort(403)
    
    page = safe_int(request.args.get('page', 1), 1)
    per_page = min(safe_int(request.args.get('per_page', 20), 20), 100)
    status = request.args.get('status', '').strip()
    assigned_to = safe_int(request.args.get('assigned_to', 0))
    
    query = Lead.query
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    
    query = query.order_by(Lead.created_at.desc())
    
    # Paginate
    result = paginate_api_query(query, page, per_page)
    result['items'] = [lead.to_dict() for lead in result['items']]
    
    return jsonify(result)

@bp.route('/leads/<int:id>')
@login_required
def get_lead(id):
    """Get specific lead"""
    if not current_user.can_access_crm():
        abort(403)
    
    lead = Lead.query.get_or_404(id)
    return jsonify(lead.to_dict())

@bp.route('/leads', methods=['POST'])
@login_required
def create_lead():
    """Create new lead"""
    if not current_user.can_access_crm():
        abort(403)
    
    data = request.get_json()
    if not data:
        abort(400)
    
    # Validate required fields
    required_fields = ['title', 'contact_name', 'contact_email']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Generate lead ID
    from app.utils.helpers import generate_lead_id
    lead_id = generate_lead_id()
    while Lead.query.filter_by(lead_id=lead_id).first():
        lead_id = generate_lead_id()
    
    try:
        lead = Lead(
            lead_id=lead_id,
            title=data['title'],
            description=data.get('description'),
            company_name=data.get('company_name'),
            contact_name=data['contact_name'],
            contact_email=data['contact_email'],
            contact_phone=data.get('contact_phone'),
            source=data.get('source'),
            priority=data.get('priority', 'medium'),
            estimated_value=data.get('estimated_value'),
            probability=data.get('probability', 0),
            assigned_to=data.get('assigned_to', current_user.id),
            created_by=current_user.id
        )
        
        db.session.add(lead)
        db.session.commit()
        
        return jsonify(lead.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/leads/<int:id>', methods=['PUT'])
@login_required
def update_lead(id):
    """Update lead information"""
    if not current_user.can_access_crm():
        abort(403)
    
    lead = Lead.query.get_or_404(id)
    data = request.get_json()
    if not data:
        abort(400)
    
    try:
        updatable_fields = ['title', 'description', 'company_name', 'contact_name',
                           'contact_email', 'contact_phone', 'source', 'status',
                           'priority', 'estimated_value', 'probability', 'assigned_to']
        
        for field in updatable_fields:
            if field in data:
                setattr(lead, field, data[field])
        
        lead.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(lead.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/leads/<int:id>', methods=['DELETE'])
@login_required
def delete_lead(id):
    """Delete lead"""
    if not current_user.can_access_crm():
        abort(403)
    
    lead = Lead.query.get_or_404(id)
    
    try:
        db.session.delete(lead)
        db.session.commit()
        return jsonify({'message': 'Lead deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Ticket API endpoints
@bp.route('/tickets')
@login_required
def get_tickets():
    """Get list of tickets"""
    if not current_user.can_access_crm():
        abort(403)
    
    page = safe_int(request.args.get('page', 1), 1)
    per_page = min(safe_int(request.args.get('per_page', 20), 20), 100)
    status = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()
    assigned_to = safe_int(request.args.get('assigned_to', 0))
    customer_id = safe_int(request.args.get('customer_id', 0))
    
    query = Ticket.query
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    
    if priority:
        query = query.filter_by(priority=priority)
    
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    
    query = query.order_by(Ticket.created_at.desc())
    
    # Paginate
    result = paginate_api_query(query, page, per_page)
    result['items'] = [ticket.to_dict() for ticket in result['items']]
    
    return jsonify(result)

@bp.route('/tickets/<int:id>')
@login_required
def get_ticket(id):
    """Get specific ticket"""
    if not current_user.can_access_crm():
        abort(403)
    
    ticket = Ticket.query.get_or_404(id)
    return jsonify(ticket.to_dict())

@bp.route('/tickets', methods=['POST'])
@login_required
def create_ticket():
    """Create new ticket"""
    if not current_user.can_access_crm():
        abort(403)
    
    data = request.get_json()
    if not data:
        abort(400)
    
    # Validate required fields
    required_fields = ['title', 'description', 'customer_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate customer exists
    customer = Customer.query.get(data['customer_id'])
    if not customer:
        return jsonify({'error': 'Customer not found'}), 400
    
    # Generate ticket ID
    from app.utils.helpers import generate_ticket_id
    ticket_id = generate_ticket_id()
    while Ticket.query.filter_by(ticket_id=ticket_id).first():
        ticket_id = generate_ticket_id()
    
    try:
        ticket = Ticket(
            ticket_id=ticket_id,
            title=data['title'],
            description=data['description'],
            customer_id=data['customer_id'],
            priority=data.get('priority', 'medium'),
            category=data.get('category'),
            assigned_to=data.get('assigned_to', current_user.id),
            created_by=current_user.id
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        return jsonify(ticket.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/tickets/<int:id>', methods=['PUT'])
@login_required
def update_ticket(id):
    """Update ticket information"""
    if not current_user.can_access_crm():
        abort(403)
    
    ticket = Ticket.query.get_or_404(id)
    data = request.get_json()
    if not data:
        abort(400)
    
    try:
        updatable_fields = ['title', 'description', 'status', 'priority', 
                           'category', 'assigned_to', 'resolution']
        
        for field in updatable_fields:
            if field in data:
                setattr(ticket, field, data[field])
        
        # Update resolved_at if status is being set to resolved
        if 'status' in data and data['status'] == 'resolved' and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
        
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(ticket.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/tickets/<int:id>', methods=['DELETE'])
@login_required
def delete_ticket(id):
    """Delete ticket"""
    if not current_user.can_access_crm():
        abort(403)
    
    ticket = Ticket.query.get_or_404(id)
    
    try:
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({'message': 'Ticket deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Job API endpoints
@bp.route('/jobs')
@login_required
def get_jobs():
    """Get list of jobs"""
    if not current_user.can_access_jobs():
        abort(403)
    
    page = safe_int(request.args.get('page', 1), 1)
    per_page = min(safe_int(request.args.get('per_page', 20), 20), 100)
    status = request.args.get('status', '').strip()
    customer_id = safe_int(request.args.get('customer_id', 0))
    assigned_to = safe_int(request.args.get('assigned_to', 0))
    
    query = Job.query
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    
    query = query.order_by(Job.created_at.desc())
    
    # Paginate
    result = paginate_api_query(query, page, per_page)
    result['items'] = [job.to_dict() for job in result['items']]
    
    return jsonify(result)

@bp.route('/jobs/<int:id>')
@login_required
def get_job(id):
    """Get specific job"""
    if not current_user.can_access_jobs():
        abort(403)
    
    job = Job.query.get_or_404(id)
    return jsonify(job.to_dict())

@bp.route('/jobs', methods=['POST'])
@login_required
def create_job():
    """Create new job"""
    if not current_user.can_access_jobs():
        abort(403)
    
    data = request.get_json()
    if not data:
        abort(400)
    
    # Validate required fields
    required_fields = ['title', 'description', 'customer_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate customer exists
    customer = Customer.query.get(data['customer_id'])
    if not customer:
        return jsonify({'error': 'Customer not found'}), 400
    
    # Generate job ID
    from app.utils.helpers import generate_job_id
    job_id = generate_job_id()
    while Job.query.filter_by(job_id=job_id).first():
        job_id = generate_job_id()
    
    try:
        job = Job(
            job_id=job_id,
            title=data['title'],
            description=data['description'],
            customer_id=data['customer_id'],
            location=data.get('location'),
            scheduled_date=datetime.strptime(data['scheduled_date'], '%Y-%m-%d %H:%M').replace(tzinfo=None) if data.get('scheduled_date') else None,
            estimated_hours=data.get('estimated_hours'),
            hourly_rate=data.get('hourly_rate'),
            priority=data.get('priority', 'medium'),
            assigned_to=data.get('assigned_to', current_user.id),
            created_by=current_user.id
        )
        
        db.session.add(job)
        db.session.commit()
        
        return jsonify(job.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/jobs/<int:id>', methods=['PUT'])
@login_required
def update_job(id):
    """Update job information"""
    if not current_user.can_access_jobs():
        abort(403)
    
    job = Job.query.get_or_404(id)
    data = request.get_json()
    if not data:
        abort(400)
    
    try:
        updatable_fields = ['title', 'description', 'location', 'status', 'priority',
                           'estimated_hours', 'actual_hours', 'hourly_rate', 'assigned_to']
        
        for field in updatable_fields:
            if field in data:
                setattr(job, field, data[field])
        
        # Handle date fields
        if 'scheduled_date' in data and data['scheduled_date']:
            job.scheduled_date = datetime.strptime(data['scheduled_date'], '%Y-%m-%d %H:%M')
        
        if 'completed_date' in data and data['completed_date']:
            job.completed_date = datetime.strptime(data['completed_date'], '%Y-%m-%d %H:%M')
        
        job.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(job.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/jobs/<int:id>', methods=['DELETE'])
@login_required
def delete_job(id):
    """Delete job"""
    if not current_user.can_access_jobs():
        abort(403)
    
    job = Job.query.get_or_404(id)
    
    try:
        db.session.delete(job)
        db.session.commit()
        return jsonify({'message': 'Job deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Dashboard/Analytics endpoints
@bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics"""
    stats = {}
    
    # HR Stats
    if current_user.can_access_hr():
        stats['employees'] = {
            'total': Employee.query.count(),
            'active': Employee.query.filter_by(status='active').count(),
            'new_this_month': Employee.query.filter(
                Employee.hire_date >= datetime.utcnow().replace(day=1).date()
            ).count()
        }
    
    # CRM Stats
    if current_user.can_access_crm():
        stats['customers'] = {
            'total': Customer.query.count(),
            'prospects': Customer.query.filter_by(customer_type='prospect').count(),
            'active': Customer.query.filter_by(customer_type='active').count()
        }
        
        stats['leads'] = {
            'total': Lead.query.count(),
            'open': Lead.query.filter_by(status='new').count() + Lead.query.filter_by(status='contacted').count(),
            'converted': Lead.query.filter_by(status='converted').count()
        }
        
        stats['tickets'] = {
            'total': Ticket.query.count(),
            'open': Ticket.query.filter_by(status='open').count(),
            'pending': Ticket.query.filter_by(status='pending').count(),
            'resolved': Ticket.query.filter_by(status='resolved').count()
        }
    
    # Job Stats
    if current_user.can_access_jobs():
        stats['jobs'] = {
            'total': Job.query.count(),
            'scheduled': Job.query.filter_by(status='scheduled').count(),
            'in_progress': Job.query.filter_by(status='in_progress').count(),
            'completed': Job.query.filter_by(status='completed').count()
        }
    
    return jsonify(stats)

# Search endpoints
@bp.route('/search')
@login_required
def global_search():
    """Global search across all entities"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400
    
    results = {
        'employees': [],
        'customers': [],
        'leads': [],
        'tickets': [],
        'jobs': []
    }
    
    # Search employees
    if current_user.can_access_hr():
        employees = Employee.query.filter(
            (Employee.first_name.contains(query)) |
            (Employee.last_name.contains(query)) |
            (Employee.email.contains(query)) |
            (Employee.employee_id.contains(query))
        ).limit(10).all()
        results['employees'] = [emp.to_dict() for emp in employees]
    
    # Search customers
    if current_user.can_access_crm():
        customers = Customer.query.filter(
            (Customer.first_name.contains(query)) |
            (Customer.last_name.contains(query)) |
            (Customer.company_name.contains(query)) |
            (Customer.email.contains(query))
        ).limit(10).all()
        results['customers'] = [customer.to_dict() for customer in customers]
        
        # Search leads
        leads = Lead.query.filter(
            (Lead.title.contains(query)) |
            (Lead.company_name.contains(query)) |
            (Lead.contact_name.contains(query)) |
            (Lead.contact_email.contains(query))
        ).limit(10).all()
        results['leads'] = [lead.to_dict() for lead in leads]
        
        # Search tickets
        tickets = Ticket.query.filter(
            (Ticket.title.contains(query)) |
            (Ticket.description.contains(query)) |
            (Ticket.ticket_id.contains(query))
        ).limit(10).all()
        results['tickets'] = [ticket.to_dict() for ticket in tickets]
    
    # Search jobs
    if current_user.can_access_jobs():
        jobs = Job.query.filter(
            (Job.title.contains(query)) |
            (Job.description.contains(query)) |
            (Job.location.contains(query)) |
            (Job.job_id.contains(query))
        ).limit(10).all()
        results['jobs'] = [job.to_dict() for job in jobs]
    
    return jsonify(results)

# Bulk operations endpoints
@bp.route('/employees/bulk', methods=['POST'])
@login_required
def bulk_employee_operations():
    """Perform bulk operations on employees"""
    if not current_user.can_access_hr():
        abort(403)
    
    data = request.get_json()
    if not data or 'action' not in data or 'employee_ids' not in data:
        abort(400)
    
    action = data['action']
    employee_ids = data['employee_ids']
    
    if not isinstance(employee_ids, list) or not employee_ids:
        return jsonify({'error': 'employee_ids must be a non-empty list'}), 400
    
    try:
        employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
        if len(employees) != len(employee_ids):
            return jsonify({'error': 'Some employees not found'}), 400
        
        if action == 'delete':
            for employee in employees:
                db.session.delete(employee)
        
        elif action == 'update_status':
            new_status = data.get('status')
            if not new_status:
                return jsonify({'error': 'Status required for update_status action'}), 400
            
            for employee in employees:
                employee.status = new_status
                employee.updated_at = datetime.utcnow()
        
        elif action == 'update_department':
            new_department = data.get('department')
            if not new_department:
                return jsonify({'error': 'Department required for update_department action'}), 400
            
            for employee in employees:
                employee.department = new_department
                employee.updated_at = datetime.utcnow()
        
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        db.session.commit()
        return jsonify({'message': f'Bulk {action} completed successfully', 'affected_count': len(employees)})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/customers/bulk', methods=['POST'])
@login_required
def bulk_customer_operations():
    """Perform bulk operations on customers"""
    if not current_user.can_access_crm():
        abort(403)
    
    data = request.get_json()
    if not data or 'action' not in data or 'customer_ids' not in data:
        abort(400)
    
    action = data['action']
    customer_ids = data['customer_ids']
    
    if not isinstance(customer_ids, list) or not customer_ids:
        return jsonify({'error': 'customer_ids must be a non-empty list'}), 400
    
    try:
        customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()
        if len(customers) != len(customer_ids):
            return jsonify({'error': 'Some customers not found'}), 400
        
        if action == 'delete':
            for customer in customers:
                db.session.delete(customer)
        
        elif action == 'update_type':
            new_type = data.get('customer_type')
            if not new_type:
                return jsonify({'error': 'customer_type required for update_type action'}), 400
            
            for customer in customers:
                customer.customer_type = new_type
                customer.updated_at = datetime.utcnow()
        
        elif action == 'assign':
            assigned_to = data.get('assigned_to')
            if not assigned_to:
                return jsonify({'error': 'assigned_to required for assign action'}), 400
            
            for customer in customers:
                customer.assigned_to = assigned_to
                customer.updated_at = datetime.utcnow()
        
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        db.session.commit()
        return jsonify({'message': f'Bulk {action} completed successfully', 'affected_count': len(customers)})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Export endpoints
@bp.route('/employees/export')
@login_required
def export_employees():
    """Export employees to CSV"""
    if not current_user.can_access_hr():
        abort(403)
    
    employees = Employee.query.all()
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Employee ID', 'First Name', 'Last Name', 'Email', 'Phone',
        'Department', 'Position', 'Hire Date', 'Employment Type',
        'Salary', 'Status', 'Created At'
    ])
    
    # Write data
    for emp in employees:
        writer.writerow([
            emp.employee_id, emp.first_name, emp.last_name, emp.email, emp.phone,
            emp.department, emp.position, emp.hire_date, emp.employment_type,
            emp.salary, emp.status, emp.created_at
        ])
    
    output.seek(0)
    
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=employees.csv'
    
    return response

@bp.route('/customers/export')
@login_required
def export_customers():
    """Export customers to CSV"""
    if not current_user.can_access_crm():
        abort(403)
    
    customers = Customer.query.all()
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Customer ID', 'Company Name', 'First Name', 'Last Name', 'Email',
        'Phone', 'Job Title', 'Industry', 'Customer Type', 'Priority',
        'Created At'
    ])
    
    # Write data
    for customer in customers:
        writer.writerow([
            customer.customer_id, customer.company_name, customer.first_name,
            customer.last_name, customer.email, customer.phone, customer.job_title,
            customer.industry, customer.customer_type, customer.priority,
            customer.created_at
        ])
    
    output.seek(0)
    
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=customers.csv'
    
    return response

# Report endpoints
@bp.route('/reports/employee-summary')
@login_required
def employee_summary_report():
    """Generate employee summary report"""
    if not current_user.can_access_hr():
        abort(403)
    
    from sqlalchemy import func
    
    # Department breakdown
    dept_stats = db.session.query(
        Employee.department,
        func.count(Employee.id).label('count')
    ).group_by(Employee.department).all()
    
    # Employment type breakdown
    type_stats = db.session.query(
        Employee.employment_type,
        func.count(Employee.id).label('count')
    ).group_by(Employee.employment_type).all()
    
    # Status breakdown
    status_stats = db.session.query(
        Employee.status,
        func.count(Employee.id).label('count')
    ).group_by(Employee.status).all()
    
    # Recent hires (last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_hires = Employee.query.filter(Employee.created_at >= thirty_days_ago).count()
    
    report = {
        'total_employees': Employee.query.count(),
        'department_breakdown': [{'department': stat[0] or 'Unassigned', 'count': stat[1]} for stat in dept_stats],
        'employment_type_breakdown': [{'type': stat[0], 'count': stat[1]} for stat in type_stats],
        'status_breakdown': [{'status': stat[0], 'count': stat[1]} for stat in status_stats],
        'recent_hires_30_days': recent_hires,
        'generated_at': datetime.utcnow().isoformat()
    }
    
    return jsonify(report)

@bp.route('/reports/customer-summary')
@login_required
def customer_summary_report():
    """Generate customer summary report"""
    if not current_user.can_access_crm():
        abort(403)
    
    from sqlalchemy import func
    
    # Customer type breakdown
    type_stats = db.session.query(
        Customer.customer_type,
        func.count(Customer.id).label('count')
    ).group_by(Customer.customer_type).all()
    
    # Industry breakdown
    industry_stats = db.session.query(
        Customer.industry,
        func.count(Customer.id).label('count')
    ).group_by(Customer.industry).all()
    
    # Priority breakdown
    priority_stats = db.session.query(
        Customer.priority,
        func.count(Customer.id).label('count')
    ).group_by(Customer.priority).all()
    
    # Recent customers (last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_customers = Customer.query.filter(Customer.created_at >= thirty_days_ago).count()
    
    report = {
        'total_customers': Customer.query.count(),
        'type_breakdown': [{'type': stat[0], 'count': stat[1]} for stat in type_stats],
        'industry_breakdown': [{'industry': stat[0] or 'Unknown', 'count': stat[1]} for stat in industry_stats],
        'priority_breakdown': [{'priority': stat[0], 'count': stat[1]} for stat in priority_stats],
        'recent_customers_30_days': recent_customers,
        'generated_at': datetime.utcnow().isoformat()
    }
    
    return jsonify(report)

# Activity log endpoints
@bp.route('/activity-log')
@login_required
def get_activity_log():
    """Get recent activity log"""
    # This would require an ActivityLog model to track all changes
    # For now, return a placeholder response
    return jsonify({
        'message': 'Activity log feature requires ActivityLog model implementation',
        'activities': []
    })

# Health check endpoint
@bp.route('/health')
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })