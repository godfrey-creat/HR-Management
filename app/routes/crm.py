"""
CRM management routes for People360
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from wtforms import Form, StringField, SelectField, TextAreaField, DateField, DecimalField, IntegerField, validators
from app import db
from app.models.customer import Customer
from app.models.lead import Lead, LeadActivity 
from app.models.ticket import Ticket, TicketResponse
from app.utils.decorators import crm_required
from app.utils.helpers import (generate_customer_id, generate_lead_id, generate_ticket_id, 
                               paginate_query, safe_int)

bp = Blueprint('crm', __name__)

# Forms
class CustomerForm(Form):
    """Customer form"""
    company_name = StringField('Company Name', [validators.Length(max=100)])
    first_name = StringField('First Name', [validators.DataRequired(), validators.Length(max=50)])
    last_name = StringField('Last Name', [validators.DataRequired(), validators.Length(max=50)])
    email = StringField('Email', [validators.DataRequired(), validators.Email()])
    phone = StringField('Phone', [validators.Length(max=20)])
    mobile = StringField('Mobile', [validators.Length(max=20)])
    job_title = StringField('Job Title', [validators.Length(max=100)])
    industry = StringField('Industry', [validators.Length(max=50)])
    company_size = SelectField('Company Size', choices=[
        ('', 'Select Size'),
        ('startup', 'Startup (1-10)'),
        ('small', 'Small (11-50)'),
        ('medium', 'Medium (51-200)'),
        ('large', 'Large (201-1000)'),
        ('enterprise', 'Enterprise (1000+)')
    ])
    website = StringField('Website', [validators.Length(max=200)])
    address_line1 = StringField('Address Line 1', [validators.Length(max=100)])
    address_line2 = StringField('Address Line 2', [validators.Length(max=100)])
    city = StringField('City', [validators.Length(max=50)])
    state = StringField('State', [validators.Length(max=50)])
    postal_code = StringField('Postal Code', [validators.Length(max=20)])
    country = StringField('Country', [validators.Length(max=50)])
    customer_type = SelectField('Customer Type', choices=[
        ('prospect', 'Prospect'),
        ('customer', 'Customer'),
        ('partner', 'Partner')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    annual_revenue = DecimalField('Annual Revenue', [validators.Optional()])
    notes = TextAreaField('Notes')
    tags = StringField('Tags (comma-separated)')

class LeadForm(Form):
    """Lead form"""
    title = StringField('Lead Title', [validators.DataRequired(), validators.Length(max=200)])
    description = TextAreaField('Description')
    customer_id = SelectField('Customer', [validators.Optional()], coerce=int)
    company_name = StringField('Company Name', [validators.Length(max=100)])
    contact_name = StringField('Contact Name', [validators.DataRequired(), validators.Length(max=100)])
    contact_email = StringField('Contact Email', [validators.DataRequired(), validators.Email()])
    contact_phone = StringField('Contact Phone', [validators.Length(max=20)])
    source = SelectField('Lead Source', choices=[
        ('', 'Select Source'),
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('cold_call', 'Cold Call'),
        ('email', 'Email Campaign'),
        ('social_media', 'Social Media'),
        ('event', 'Event/Trade Show'),
        ('advertisement', 'Advertisement'),
        ('partner', 'Partner')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ])
    estimated_value = DecimalField('Estimated Value', [validators.Optional()])
    probability = IntegerField('Probability (%)', [validators.Optional(), validators.NumberRange(min=0, max=100)])
    expected_close_date = DateField('Expected Close Date', [validators.Optional()])
    assigned_to = SelectField('Assigned To', [validators.Optional()], coerce=int)
    budget = DecimalField('Budget', [validators.Optional()])
    decision_maker = StringField('Decision Maker', [validators.Length(max=100)])
    timeline = StringField('Timeline', [validators.Length(max=100)])
    pain_points = TextAreaField('Pain Points')
    solution_fit = TextAreaField('Solution Fit')
    competitors = StringField('Competitors (comma-separated)')
    notes = TextAreaField('Notes')
    tags = StringField('Tags (comma-separated)')

class TicketForm(Form):
    """Support ticket form"""
    subject = StringField('Subject', [validators.DataRequired(), validators.Length(max=200)])
    description = TextAreaField('Description', [validators.DataRequired()])
    customer_id = SelectField('Customer', [validators.Optional()], coerce=int)
    customer_name = StringField('Customer Name', [validators.DataRequired(), validators.Length(max=100)])
    customer_email = StringField('Customer Email', [validators.DataRequired(), validators.Email()])
    customer_phone = StringField('Customer Phone', [validators.Length(max=20)])
    category = SelectField('Category', choices=[
        ('', 'Select Category'),
        ('technical', 'Technical Support'),
        ('billing', 'Billing/Account'),
        ('general', 'General Inquiry'),
        ('feature_request', 'Feature Request'),
        ('bug_report', 'Bug Report'),
        ('training', 'Training/How-to')
    ])
    subcategory = StringField('Subcategory', [validators.Length(max=50)])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ])
    severity = SelectField('Severity', choices=[
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical'),
        ('blocker', 'System Down')
    ])
    assigned_to = SelectField('Assigned To', [validators.Optional()], coerce=int)
    channel = SelectField('Channel', choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('chat', 'Live Chat'),
        ('portal', 'Customer Portal'),
        ('social', 'Social Media')
    ])

# Customer Routes
@bp.route('/customers')
@crm_required
def customers():
    """List all customers"""
    page = safe_int(request.args.get('page', 1), 1)
    search = request.args.get('search', '').strip()
    customer_type = request.args.get('customer_type', '').strip()
    priority = request.args.get('priority', '').strip()
    
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
    
    if priority:
        query = query.filter_by(priority=priority)
    
    # Order by creation date
    query = query.order_by(Customer.created_at.desc())
    
    # Paginate
    customers_pagination = paginate_query(query, page, 20)
    
    return render_template('crm/customers.html',
                         customers=customers_pagination.items,
                         pagination=customers_pagination,
                         search=search,
                         selected_customer_type=customer_type,
                         selected_priority=priority)

@bp.route('/customers/add', methods=['GET', 'POST'])
@crm_required
def add_customer():
    """Add new customer"""
    form = CustomerForm(request.form)
    
    if request.method == 'POST' and form.validate():
        # Generate customer ID
        customer_id = generate_customer_id()
        while Customer.query.filter_by(customer_id=customer_id).first():
            customer_id = generate_customer_id()
        
        customer = Customer(
            customer_id=customer_id,
            company_name=form.company_name.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            mobile=form.mobile.data,
            job_title=form.job_title.data,
            industry=form.industry.data,
            company_size=form.company_size.data,
            website=form.website.data,
            address_line1=form.address_line1.data,
            address_line2=form.address_line2.data,
            city=form.city.data,
            state=form.state.data,
            postal_code=form.postal_code.data,
            country=form.country.data,
            customer_type=form.customer_type.data,
            priority=form.priority.data,
            annual_revenue=form.annual_revenue.data,
            notes=form.notes.data,
            tags=form.tags.data,
            assigned_to=current_user.id,
            created_by=current_user.id
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash(f'Customer {customer.display_name} added successfully!', 'success')
        return redirect(url_for('crm.customers'))
    
    return render_template('crm/customer_form.html', form=form, title='Add Customer')

@bp.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@crm_required
def edit_customer(id):
    """Edit customer"""
    customer = Customer.query.get_or_404(id)
    form = CustomerForm(request.form, obj=customer)
    
    if request.method == 'POST' and form.validate():
        form.populate_obj(customer)
        customer.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Customer {customer.display_name} updated successfully!', 'success')
        return redirect(url_for('crm.customers'))
    
    return render_template('crm/customer_form.html', 
                         form=form, 
                         customer=customer, 
                         title='Edit Customer')

@bp.route('/customers/<int:id>')
@crm_required
def view_customer(id):
    """View customer details"""
    customer = Customer.query.get_or_404(id)
    
    # Get related leads and tickets
    leads = customer.leads.order_by(Lead.created_at.desc()).limit(10).all()
    tickets = customer.tickets.order_by(Ticket.created_at.desc()).limit(10).all()
    
    return render_template('crm/customer_detail.html', 
                         customer=customer,
                         leads=leads,
                         tickets=tickets)

# Lead Routes
@bp.route('/leads')
@crm_required
def leads():
    """List all leads"""
    page = safe_int(request.args.get('page', 1), 1)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()
    assigned_to = safe_int(request.args.get('assigned_to', 0))
    
    query = Lead.query
    
    # Apply filters
    if search:
        query = query.filter(
            (Lead.title.contains(search)) |
            (Lead.contact_name.contains(search)) |
            (Lead.company_name.contains(search)) |
            (Lead.contact_email.contains(search)) |
            (Lead.lead_id.contains(search))
        )
    
    if status:
        query = query.filter_by(status=status)
    
    if priority:
        query = query.filter_by(priority=priority)
    
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    
    # Order by creation date
    query = query.order_by(Lead.created_at.desc())
    
    # Paginate
    leads_pagination = paginate_query(query, page, 20)
    
    # Get users for assignment filter
    from app.models import User
    users = User.query.filter(User.role.in_(['admin', 'sales_manager', 'support_agent'])).all()
    
    return render_template('crm/leads.html',
                         leads=leads_pagination.items,
                         pagination=leads_pagination,
                         users=users,
                         search=search,
                         selected_status=status,
                         selected_priority=priority,
                         selected_assigned_to=assigned_to)

@bp.route('/leads/add', methods=['GET', 'POST'])
@crm_required
def add_lead():
    """Add new lead"""
    form = LeadForm(request.form)
    
    # Populate customer choices
    customers = Customer.query.filter_by(status='active').all()
    form.customer_id.choices = [('', 'No Customer')] + [(c.id, c.display_name) for c in customers]
    
    # Populate assignment choices
    from app.models import User
    users = User.query.filter(User.role.in_(['admin', 'sales_manager', 'support_agent'])).all()
    form.assigned_to.choices = [('', 'Unassigned')] + [(u.id, u.full_name) for u in users]
    
    if request.method == 'POST' and form.validate():
        # Generate lead ID
        lead_id = generate_lead_id()
        while Lead.query.filter_by(lead_id=lead_id).first():
            lead_id = generate_lead_id()
        
        lead = Lead(
            lead_id=lead_id,
            title=form.title.data,
            description=form.description.data,
            customer_id=form.customer_id.data if form.customer_id.data else None,
            company_name=form.company_name.data,
            contact_name=form.contact_name.data,
            contact_email=form.contact_email.data,
            contact_phone=form.contact_phone.data,
            source=form.source.data,
            priority=form.priority.data,
            estimated_value=form.estimated_value.data,
            probability=form.probability.data,
            expected_close_date=form.expected_close_date.data,
            assigned_to=form.assigned_to.data if form.assigned_to.data else None,
            budget=form.budget.data,
            decision_maker=form.decision_maker.data,
            timeline=form.timeline.data,
            pain_points=form.pain_points.data,
            solution_fit=form.solution_fit.data,
            competitors=form.competitors.data,
            notes=form.notes.data,
            tags=form.tags.data,
            created_by=current_user.id
        )
        
        db.session.add(lead)
        db.session.commit()
        
        flash(f'Lead "{lead.title}" created successfully!', 'success')
        return redirect(url_for('crm.leads'))
    
    return render_template('crm/lead_form.html', form=form, title='Add Lead')

@bp.route('/leads/<int:id>/edit', methods=['GET', 'POST'])
@crm_required
def edit_lead(id):
    """Edit lead"""
    lead = Lead.query.get_or_404(id)
    form = LeadForm(request.form, obj=lead)
    
    # Populate choices
    customers = Customer.query.filter_by(status='active').all()
    form.customer_id.choices = [('', 'No Customer')] + [(c.id, c.display_name) for c in customers]
    
    from app.models import User
    users = User.query.filter(User.role.in_(['admin', 'sales_manager', 'support_agent'])).all()
    form.assigned_to.choices = [('', 'Unassigned')] + [(u.id, u.full_name) for u in users]
    
    if request.method == 'POST' and form.validate():
        form.populate_obj(lead)
        lead.customer_id = form.customer_id.data if form.customer_id.data else None
        lead.assigned_to = form.assigned_to.data if form.assigned_to.data else None
        lead.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Lead "{lead.title}" updated successfully!', 'success')
        return redirect(url_for('crm.leads'))
    
    return render_template('crm/lead_form.html', 
                         form=form, 
                         lead=lead, 
                         title='Edit Lead')

@bp.route('/leads/<int:id>')
@crm_required
def view_lead(id):
    """View lead details"""
    lead = Lead.query.get_or_404(id)
    
    # Get activities
    activities = lead.activities.order_by(LeadActivity.created_at.desc()).limit(20).all()
    
    return render_template('crm/lead_detail.html', 
                         lead=lead,
                         activities=activities)

@bp.route('/leads/<int:id>/status/<status>')
@crm_required
def update_lead_status(id, status):
    """Update lead status"""
    lead = Lead.query.get_or_404(id)
    
    if status in ['new', 'qualified', 'proposal', 'negotiation', 'won', 'lost']:
        old_status = lead.status
        lead.status = status
        
        # Update stage based on status
        stage_mapping = {
            'new': 'Initial Contact',
            'qualified': 'Qualification',
            'proposal': 'Proposal',
            'negotiation': 'Negotiation',
            'won': 'Closed Won',
            'lost': 'Closed Lost'
        }
        lead.stage = stage_mapping.get(status, lead.stage)
        
        # Set close date if won or lost
        if status in ['won', 'lost']:
            lead.actual_close_date = date.today()
        
        # Create activity
        activity = LeadActivity(
            lead_id=lead.id,
            activity_type='status_change',
            subject=f'Status changed from {old_status} to {status}',
            description=f'Lead status updated by {current_user.full_name}',
            created_by=current_user.id
        )
        
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Lead status updated to {lead.get_status_display()}!', 'success')
    else:
        flash('Invalid status!', 'error')
    
    return redirect(url_for('crm.view_lead', id=id))

# Ticket Routes
@bp.route('/tickets')
@crm_required
def tickets():
    """List all support tickets"""
    page = safe_int(request.args.get('page', 1), 1)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()
    assigned_to = safe_int(request.args.get('assigned_to', 0))
    
    query = Ticket.query
    
    # Apply filters
    if search:
        query = query.filter(
            (Ticket.subject.contains(search)) |
            (Ticket.customer_name.contains(search)) |
            (Ticket.customer_email.contains(search)) |
            (Ticket.ticket_id.contains(search))
        )
    
    if status:
        query = query.filter_by(status=status)
    
    if priority:
        query = query.filter_by(priority=priority)
    
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    
    # Order by creation date
    query = query.order_by(Ticket.created_at.desc())
    
    # Paginate
    tickets_pagination = paginate_query(query, page, 20)
    
    # Get users for assignment filter
    from app.models import User
    users = User.query.filter(User.role.in_(['admin', 'sales_manager', 'support_agent'])).all()
    
    return render_template('crm/tickets.html',
                         tickets=tickets_pagination.items,
                         pagination=tickets_pagination,
                         users=users,
                         search=search,
                         selected_status=status,
                         selected_priority=priority,
                         selected_assigned_to=assigned_to)

@bp.route('/tickets/add', methods=['GET', 'POST'])
@crm_required
def add_ticket():
    """Add new support ticket"""
    form = TicketForm(request.form)
    
    # Populate customer choices
    customers = Customer.query.filter_by(status='active').all()
    form.customer_id.choices = [('', 'No Customer')] + [(c.id, c.display_name) for c in customers]
    
    # Populate assignment choices
    from app.models import User
    users = User.query.filter(User.role.in_(['admin', 'sales_manager', 'support_agent'])).all()
    form.assigned_to.choices = [('', 'Unassigned')] + [(u.id, u.full_name) for u in users]
    
    if request.method == 'POST' and form.validate():
        # Generate ticket ID
        ticket_id = generate_ticket_id()
        while Ticket.query.filter_by(ticket_id=ticket_id).first():
            ticket_id = generate_ticket_id()
        
        ticket = Ticket(
            ticket_id=ticket_id,
            subject=form.subject.data,
            description=form.description.data,
            customer_id=form.customer_id.data if form.customer_id.data else None,
            customer_name=form.customer_name.data,
            customer_email=form.customer_email.data,
            customer_phone=form.customer_phone.data,
            category=form.category.data,
            subcategory=form.subcategory.data,
            priority=form.priority.data,
            severity=form.severity.data,
            assigned_to=form.assigned_to.data if form.assigned_to.data else None,
            channel=form.channel.data,
            created_by=current_user.id
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        flash(f'Support ticket "{ticket.subject}" created successfully!', 'success')
        return redirect(url_for('crm.tickets'))
    
    return render_template('crm/ticket_form.html', form=form, title='Add Ticket')

@bp.route('/tickets/<int:id>')
@crm_required
def view_ticket(id):
    """View ticket details"""
    ticket = Ticket.query.get_or_404(id)
    
    # Get responses
    responses = ticket.responses.order_by(TicketResponse.created_at.asc()).all()
    
    return render_template('crm/ticket_detail.html', 
                         ticket=ticket,
                         responses=responses)

@bp.route('/tickets/<int:id>/status/<status>')
@crm_required
def update_ticket_status(id, status):
    """Update ticket status"""
    ticket = Ticket.query.get_or_404(id)
    
    if status in ['open', 'in_progress', 'waiting', 'resolved', 'closed']:
        ticket.status = status
        
        if status == 'resolved':
            ticket.resolution_date = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Ticket status updated to {ticket.get_status_display()}!', 'success')
    else:
        flash('Invalid status!', 'error')
    
    return redirect(url_for('crm.view_ticket', id=id))

# API Routes
@bp.route('/api/customers')
@crm_required
def api_customers():
    """API endpoint for customers"""
    customers = Customer.query.filter_by(status='active').all()
    return jsonify([customer.to_dict() for customer in customers])

@bp.route('/api/leads')
@crm_required
def api_leads():
    """API endpoint for leads"""
    leads = Lead.query.all()
    return jsonify([lead.to_dict() for lead in leads])

@bp.route('/api/tickets')
@crm_required
def api_tickets():
    """API endpoint for tickets"""
    tickets = Ticket.query.all()
    return jsonify([ticket.to_dict() for ticket in tickets])