#!/usr/bin/env python3
import os
from app import create_app, db
from app.models import User, Employee, Department, Attendance, LeaveRequest

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Employee=Employee, Department=Department, 
                Attendance=Attendance, LeaveRequest=LeaveRequest)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)