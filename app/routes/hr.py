"""
HR management routes for People360
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from wtforms import Form, StringField, SelectField, TextAreaField, DateField, DecimalField, IntegerField, validators
from app import db
from app.models.employees import Employee, TimeOff
from app.models.job import Job, JobApplication
from app.utils.decorators import hr_required
from app.utils.helpers import generate_employee_id, generate_job_id, generate_application_id, paginate_query, safe_int

bp = Blueprint('hr', __name__)

# Forms
class EmployeeForm(Form):
    """Employee form"""
    first_name = StringField('First Name', [validators.DataRequired(), validators.Length(max=50)])
    last_name = StringField('Last Name', [validators.DataRequired(), validators.Length(max=50)])
    email = StringField('Email', [validators.DataRequired(), validators.Email()])
    phone = StringField('Phone', [validators.Length(max=20)])
    date_of_birth = DateField('Date of Birth', [validators.Optional()])
    address = TextAreaField('Address')
    emergency_contact = StringField('Emergency Contact', [validators.Length(max=100)])
    emergency_phone = StringField('Emergency Phone', [validators.Length(max=20)])
    department = StringField('Department', [validators.Length(max=50)])
    position = StringField('Position', [validators.DataRequired(), validators.Length(max=100)])
    hire_date = DateField('Hire Date', [validators.DataRequired()], default=date.today)
    employment_type = SelectField('Employment Type', choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern')
    ])
    salary = DecimalField('Salary', [validators.Optional()])
    salary_type = SelectField('Salary Type', choices=[
        ('hourly', 'Hourly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ])
    manager_id = SelectField('Manager', [validators.Optional()], coerce=int)

class JobForm(Form):
    """Job posting form"""
    title = StringField('Job Title', [validators.DataRequired(), validators.Length(max=100)])
    department = StringField('Department', [validators.DataRequired(), validators.Length(max=50)])
    location = StringField('Location', [validators.Length(max=100)])
    employment_type = SelectField('Employment Type', choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship')
    ])
    experience_level = SelectField('Experience Level', choices=[
        ('entry', 'Entry Level'),
        ('mid_level', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive')
    ])
    description = TextAreaField('Job Description', [validators.DataRequired()])
    requirements = TextAreaField('Requirements')
    responsibilities = TextAreaField('Responsibilities')
    benefits = TextAreaField('Benefits')
    salary_min = DecimalField('Minimum Salary', [validators.Optional()])
    salary_max = DecimalField('Maximum Salary', [validators.Optional()])
    positions_available = IntegerField('Positions Available', [validators.DataRequired()], default=1)
    closing_date = DateField('Application Closing Date', [validators.Optional()])

# Employee Routes
@bp.route('/employees')
@hr_required
def employees():
    """List all employees"""
    page = safe_int(request.args.get('page', 1), 1)
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
    
    # Order by creation date
    query = query.order_by(Employee.created_at.desc())
    
    # Paginate
    employees_pagination = paginate_query(query, page, 20)
    
    # Get departments for filter dropdown
    departments = db.session.query(Employee.department).filter(
        Employee.department.isnot(None)
    ).distinct().all()
    departments = [dept[0] for dept in departments]
    
    return render_template('hr/employees.html',
                         employees=employees_pagination.items,
                         pagination=employees_pagination,
                         departments=departments,
                         search=search,
                         selected_department=department,
                         selected_status=status)

@bp.route('/employees/add', methods=['GET', 'POST'])
@hr_required
def add_employee():
    """Add new employee"""
    form = EmployeeForm(request.form)
    
    # Populate manager choices
    managers = Employee.query.filter_by(status='active').all()
    form.manager_id.choices = [('', 'No Manager')] + [(m.id, m.full_name) for m in managers]
    
    if request.method == 'POST' and form.validate():
        # Generate employee ID
        employee_id = generate_employee_id()
        while Employee.query.filter_by(employee_id=employee_id).first():
            employee_id = generate_employee_id()
        
        employee = Employee(
            employee_id=employee_id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            date_of_birth=form.date_of_birth.data,
            address=form.address.data,
            emergency_contact=form.emergency_contact.data,
            emergency_phone=form.emergency_phone.data,
            department=form.department.data,
            position=form.position.data,
            hire_date=form.hire_date.data,
            employment_type=form.employment_type.data,
            salary=form.salary.data,
            salary_type=form.salary_type.data,
            manager_id=form.manager_id.data if form.manager_id.data else None,
            created_by=current_user.id
        )
        
        db.session.add(employee)
        db.session.commit()
        
        flash(f'Employee {employee.full_name} added successfully!', 'success')
        return redirect(url_for('hr.employees'))
    
    return render_template('hr/employee_form.html', form=form, title='Add Employee')

@bp.route('/employees/<int:id>/edit', methods=['GET', 'POST'])
@hr_required
def edit_employee(id):
    """Edit employee"""
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(request.form, obj=employee)
    
    # Populate manager choices (exclude self)
    managers = Employee.query.filter(
        Employee.status == 'active',
        Employee.id != employee.id
    ).all()
    form.manager_id.choices = [('', 'No Manager')] + [(m.id, m.full_name) for m in managers]
    
    if request.method == 'POST' and form.validate():
        form.populate_obj(employee)
        employee.manager_id = form.manager_id.data if form.manager_id.data else None
        employee.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Employee {employee.full_name} updated successfully!', 'success')
        return redirect(url_for('hr.employees'))
    
    return render_template('hr/employee_form.html', 
                         form=form, 
                         employee=employee, 
                         title='Edit Employee')

@bp.route('/employees/<int:id>')
@hr_required
def view_employee(id):
    """View employee details"""
    employee = Employee.query.get_or_404(id)
    
    # Get time-off requests
    timeoff_requests = TimeOff.query.filter_by(employee_id=id).order_by(
        TimeOff.created_at.desc()
    ).limit(10).all()
    
    return render_template('hr/employee_detail.html', 
                         employee=employee,
                         timeoff_requests=timeoff_requests)

# Job Routes
@bp.route('/jobs')
@hr_required
def jobs():
    """List all jobs"""
    page = safe_int(request.args.get('page', 1), 1)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    
    query = Job.query
    
    # Apply filters
    if search:
        query = query.filter(
            (Job.title.contains(search)) |
            (Job.department.contains(search)) |
            (Job.job_id.contains(search))
        )
    
    if status:
        query = query.filter_by(status=status)
    
    # Order by creation date
    query = query.order_by(Job.created_at.desc())
    
    # Paginate
    jobs_pagination = paginate_query(query, page, 20)
    
    return render_template('hr/jobs.html',
                         jobs=jobs_pagination.items,
                         pagination=jobs_pagination,
                         search=search,
                         selected_status=status)

@bp.route('/jobs/add', methods=['GET', 'POST'])
@hr_required
def add_job():
    """Add new job posting"""
    form = JobForm(request.form)
    
    if request.method == 'POST' and form.validate():
        # Generate job ID
        job_id = generate_job_id()
        while Job.query.filter_by(job_id=job_id).first():
            job_id = generate_job_id()
        
        job = Job(
            job_id=job_id,
            title=form.title.data,
            department=form.department.data,
            location=form.location.data,
            employment_type=form.employment_type.data,
            experience_level=form.experience_level.data,
            description=form.description.data,
            requirements=form.requirements.data,
            responsibilities=form.responsibilities.data,
            benefits=form.benefits.data,
            salary_min=form.salary_min.data,
            salary_max=form.salary_max.data,
            positions_available=form.positions_available.data,
            closing_date=form.closing_date.data,
            posted_by=current_user.id,
            hiring_manager_id=current_user.id
        )
        
        db.session.add(job)
        db.session.commit()
        
        flash(f'Job "{job.title}" created successfully!', 'success')
        return redirect(url_for('hr.jobs'))
    
    return render_template('hr/job_form.html', form=form, title='Add Job')

@bp.route('/jobs/<int:id>/edit', methods=['GET', 'POST'])
@hr_required
def edit_job(id):
    """Edit job posting"""
    job = Job.query.get_or_404(id)
    form = JobForm(request.form, obj=job)
    
    if request.method == 'POST' and form.validate():
        form.populate_obj(job)
        job.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Job "{job.title}" updated successfully!', 'success')
        return redirect(url_for('hr.jobs'))
    
    return render_template('hr/job_form.html', 
                         form=form, 
                         job=job, 
                         title='Edit Job')

@bp.route('/jobs/<int:id>')
@hr_required
def view_job(id):
    """View job details and applications"""
    job = Job.query.get_or_404(id)
    
    # Get applications
    applications = job.applications.order_by(JobApplication.applied_at.desc()).all()
    
    return render_template('hr/job_detail.html', 
                         job=job, 
                         applications=applications)

@bp.route('/jobs/<int:id>/publish')
@hr_required
def publish_job(id):
    """Publish job posting"""
    job = Job.query.get_or_404(id)
    job.status = 'published'
    job.published_date = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Job "{job.title}" published successfully!', 'success')
    return redirect(url_for('hr.view_job', id=id))

@bp.route('/jobs/<int:id>/close')
@hr_required
def close_job(id):
    """Close job posting"""
    job = Job.query.get_or_404(id)
    job.status = 'closed'
    
    db.session.commit()
    
    flash(f'Job "{job.title}" closed successfully!', 'info')
    return redirect(url_for('hr.view_job', id=id))

# Application Routes
@bp.route('/applications/<int:id>')
@hr_required
def view_application(id):
    """View job application details"""
    application = JobApplication.query.get_or_404(id)
    
    return render_template('hr/application_detail.html', application=application)

@bp.route('/applications/<int:id>/status/<status>')
@hr_required
def update_application_status(id, status):
    """Update application status"""
    application = JobApplication.query.get_or_404(id)
    
    if status in ['screening', 'interviewed', 'offered', 'hired', 'rejected']:
        application.status = status
        application.reviewed_by = current_user.id
        application.reviewed_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Application status updated to {application.get_status_display()}!', 'success')
    else:
        flash('Invalid status!', 'error')
    
    return redirect(url_for('hr.view_application', id=id))

# API Routes
@bp.route('/api/employees')
@hr_required
def api_employees():
    """API endpoint for employees"""
    employees = Employee.query.filter_by(status='active').all()
    return jsonify([emp.to_dict() for emp in employees])

@bp.route('/api/jobs')
@hr_required
def api_jobs():
    """API endpoint for jobs"""
    jobs = Job.query.all()
    return jsonify([job.to_dict() for job in jobs])