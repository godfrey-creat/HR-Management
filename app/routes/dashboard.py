"""
Dashboard routes for People360
"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import User, Employee, Customer, Job, Lead, Ticket

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """Main dashboard"""
    # Get dashboard statistics based on user role
    stats = get_dashboard_stats()
    recent_activities = get_recent_activities()
    
    return render_template('dashboard/index.html', 
                         stats=stats, 
                         recent_activities=recent_activities)

def get_dashboard_stats():
    """Get dashboard statistics based on user role"""
    stats = {}
    
    # Common stats for all users
    stats['total_employees'] = Employee.query.filter_by(status='active').count()
    stats['total_customers'] = Customer.query.filter_by(status='active').count()
    
    # Role-specific stats
    if current_user.can_access_hr():
        # HR Statistics
        stats['open_positions'] = Job.query.filter_by(status='published').count()
        stats['pending_applications'] = db.session.query(func.count()).select_from(
            db.session.query(Job).join(Job.applications).filter(
                Job.status == 'published'
            ).subquery()
        ).scalar() or 0
        
        # Recent hires (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        stats['recent_hires'] = Employee.query.filter(
            Employee.hire_date >= thirty_days_ago.date()
        ).count()
        
        # Time-off requests pending approval
        from app.models.employees import TimeOff
        stats['pending_timeoff'] = TimeOff.query.filter_by(status='pending').count()
    
    if current_user.can_access_crm():
        # CRM Statistics
        stats['active_leads'] = Lead.query.filter(
            Lead.status.in_(['new', 'qualified', 'proposal', 'negotiation'])
        ).count()
        
        stats['open_tickets'] = Ticket.query.filter_by(status='open').count()
        
        # Monthly sales pipeline value
        stats['pipeline_value'] = db.session.query(func.sum(Lead.estimated_value)).filter(
            Lead.status.in_(['qualified', 'proposal', 'negotiation'])
        ).scalar() or 0
        
        # Overdue tickets
        overdue_tickets = 0
        for ticket in Ticket.query.filter(Ticket.status.in_(['open', 'in_progress'])).all():
            if ticket.is_overdue():
                overdue_tickets += 1
        stats['overdue_tickets'] = overdue_tickets
    
    return stats

def get_recent_activities():
    """Get recent system activities"""
    activities = []
    
    # Recent employees added (last 7 days)
    if current_user.can_access_hr():
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_employees = Employee.query.filter(
            Employee.created_at >= seven_days_ago
        ).order_by(Employee.created_at.desc()).limit(5).all()
        
        for emp in recent_employees:
            activities.append({
                'type': 'employee_added',
                'message': f'New employee {emp.full_name} added to {emp.department}',
                'timestamp': emp.created_at,
                'icon': 'user-plus',
                'url': f'/hr/employees/{emp.id}'
            })
    
    # Recent customers added
    if current_user.can_access_crm():
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_customers = Customer.query.filter(
            Customer.created_at >= seven_days_ago
        ).order_by(Customer.created_at.desc()).limit(5).all()
        
        for customer in recent_customers:
            activities.append({
                'type': 'customer_added',
                'message': f'New customer {customer.display_name} added',
                'timestamp': customer.created_at,
                'icon': 'user-check',
                'url': f'/crm/customers/{customer.id}'
            })
        
        # Recent leads
        recent_leads = Lead.query.filter(
            Lead.created_at >= seven_days_ago
        ).order_by(Lead.created_at.desc()).limit(5).all()
        
        for lead in recent_leads:
            activities.append({
                'type': 'lead_created',
                'message': f'New lead: {lead.title} (${lead.estimated_value:,.0f})',
                'timestamp': lead.created_at,
                'icon': 'trending-up',
                'url': f'/crm/leads/{lead.id}'
            })
    
    # Sort activities by timestamp and limit to 10
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:10]

@bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """API endpoint for dashboard statistics"""
    return jsonify(get_dashboard_stats())

@bp.route('/api/dashboard/activities')
@login_required
def api_dashboard_activities():
    """API endpoint for recent activities"""
    return jsonify(get_recent_activities())

@bp.route('/api/dashboard/charts/employees')
@login_required
def api_employees_chart():
    """API endpoint for employees chart data"""
    if not current_user.can_access_hr():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Employee count by department
    dept_stats = db.session.query(
        Employee.department,
        func.count(Employee.id).label('count')
    ).filter_by(status='active').group_by(Employee.department).all()
    
    chart_data = {
        'labels': [dept[0] or 'Unassigned' for dept in dept_stats],
        'data': [dept[1] for dept in dept_stats]
    }
    
    return jsonify(chart_data)

@bp.route('/api/dashboard/charts/leads')
@login_required
def api_leads_chart():
    """API endpoint for leads pipeline chart data"""
    if not current_user.can_access_crm():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Leads by status
    status_stats = db.session.query(
        Lead.status,
        func.count(Lead.id).label('count'),
        func.sum(Lead.estimated_value).label('total_value')
    ).group_by(Lead.status).all()
    
    chart_data = {
        'labels': [Lead.STATUSES.get(stat[0], stat[0].title()) for stat in status_stats],
        'counts': [stat[1] for stat in status_stats],
        'values': [float(stat[2] or 0) for stat in status_stats]
    }
    
    return jsonify(chart_data)

@bp.route('/api/dashboard/charts/tickets')
@login_required
def api_tickets_chart():
    """API endpoint for tickets chart data"""
    if not current_user.can_access_crm():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Tickets by status
    status_stats = db.session.query(
        Ticket.status,
        func.count(Ticket.id).label('count')
    ).group_by(Ticket.status).all()
    
    # Tickets by priority
    priority_stats = db.session.query(
        Ticket.priority,
        func.count(Ticket.id).label('count')
    ).filter(Ticket.status.in_(['open', 'in_progress'])).group_by(Ticket.priority).all()
    
    chart_data = {
        'status': {
            'labels': [Ticket.STATUSES.get(stat[0], stat[0].title()) for stat in status_stats],
            'data': [stat[1] for stat in status_stats]
        },
        'priority': {
            'labels': [Ticket.PRIORITIES.get(stat[0], stat[0].title()) for stat in priority_stats],
            'data': [stat[1] for stat in priority_stats]
        }
    }
    
    return jsonify(chart_data)