#!/usr/bin/env python3
"""
People360 - Unified HRM-CRM Platform
Main application entry point
"""

from app import create_app, db
from app.models import User, Employee, Customer, Job, Lead, Ticket
import os

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Employee': Employee,
        'Customer': Customer,
        'Job': Job,
        'Lead': Lead,
        'Ticket': Ticket
    }

@app.cli.command()
def create_admin():
    """Create an admin user"""
    from werkzeug.security import generate_password_hash
    
    admin = User(
        username='admin',
        email='admin@people360.com',
        password_hash=generate_password_hash('admin123'),
        role='admin',
        is_active=True
    )
    
    db.session.add(admin)
    db.session.commit()
    print('Admin user created successfully!')

@app.cli.command()
def init_db():
    """Initialize the database with sample data"""
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        create_admin.callback()
    
    print('Database initialized!')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)