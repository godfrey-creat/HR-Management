# ============================================================================
# File: app/services/payroll_service.py
# Payroll Business Logic
# ============================================================================

from datetime import datetime, date, timedelta
from app import db
from app.models import Employee, PayrollRecord, Attendance
from sqlalchemy import and_
import calendar


def calculate_working_days(start_date: date, end_date: date) -> int:
    """Utility function to calculate working days (Mon–Fri) between two dates"""
    working_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 0 = Monday, 6 = Sunday
            working_days += 1
        current += timedelta(days=1)
    return working_days


class PayrollService:
    
    @staticmethod
    def calculate_monthly_payroll(employee_id, month, year):
        """Calculate monthly payroll for an employee"""
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        # Get attendance records for the month
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]  # last day of month
        end_date = date(year, month, last_day)
        
        attendance_records = Attendance.query.filter(
            and_(
                Attendance.employee_id == employee_id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
        ).all()
        
        # Calculate working days and hours
        total_working_days = calculate_working_days(start_date, end_date)
        actual_working_days = len([a for a in attendance_records if a.status == 'present'])
        total_hours = sum([float(a.total_hours or 0) for a in attendance_records])
        
        # Basic salary calculation
        basic_salary = float(employee.salary or 0)
        daily_rate = basic_salary / 30  # Flat assumption; can be replaced with actual calendar days
        
        # Calculate deductions for absences
        absent_days = max(0, total_working_days - actual_working_days)
        absence_deduction = absent_days * daily_rate
        
        # Calculate overtime
        regular_hours_per_day = 8
        expected_hours = actual_working_days * regular_hours_per_day
        overtime_hours = max(0, total_hours - expected_hours)
        overtime_rate = (daily_rate / 8) * 1.5  # 1.5x for overtime
        overtime_amount = overtime_hours * overtime_rate
        
        # Allowances (could be configurable per employee)
        allowances = basic_salary * 0.1  # Example: 10% of basic salary
        
        # Gross pay
        gross_pay = basic_salary + allowances + overtime_amount - absence_deduction
        
        # Tax calculation (simplified)
        tax_rate = 0.15 if gross_pay > 50000 else 0.10
        tax_deduction = gross_pay * tax_rate
        
        # Other deductions (configurable in real systems)
        other_deductions = gross_pay * 0.05  # Example: 5%
        
        # Net pay
        net_pay = gross_pay - tax_deduction - other_deductions
        
        return {
            'basic_salary': basic_salary,
            'allowances': allowances,
            'overtime_amount': overtime_amount,
            'gross_pay': gross_pay,
            'tax_deduction': tax_deduction,
            'other_deductions': other_deductions,
            'net_pay': net_pay,
            'working_days': total_working_days,
            'actual_days': actual_working_days,
            'total_hours': total_hours,
            'overtime_hours': overtime_hours
        }
    
    @staticmethod
    def create_payroll_record(employee_id, pay_period_start, pay_period_end):
        """Create a payroll record for an employee"""
        payroll_data = PayrollService.calculate_monthly_payroll(
            employee_id, 
            pay_period_start.month, 
            pay_period_start.year
        )
        
        payroll_record = PayrollRecord(
            employee_id=employee_id,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            basic_salary=payroll_data['basic_salary'],
            allowances=payroll_data['allowances'],
            overtime_amount=payroll_data['overtime_amount'],
            gross_pay=payroll_data['gross_pay'],
            tax_deduction=payroll_data['tax_deduction'],
            other_deductions=payroll_data['other_deductions'],
            net_pay=payroll_data['net_pay']
        )
        
        db.session.add(payroll_record)
        db.session.commit()
        
        return payroll_record
    
    @staticmethod
    def generate_payslip_data(payroll_record_id):
        """Generate payslip data for PDF generation"""
        record = PayrollRecord.query.get(payroll_record_id)
        if not record:
            raise ValueError("Payroll record not found")
        
        employee = record.employee
        
        return {
            'employee': {
                'name': f"{employee.first_name} {employee.last_name}",
                'employee_id': employee.employee_id,
                'position': employee.position,
                'department': employee.department.name if employee.department else 'N/A'
            },
            'pay_period': {
                'start': record.pay_period_start.strftime('%Y-%m-%d'),
                'end': record.pay_period_end.strftime('%Y-%m-%d')
            },
            'earnings': {
                'basic_salary': float(record.basic_salary),
                'allowances': float(record.allowances),
                'overtime': float(record.overtime_amount),
                'gross_pay': float(record.gross_pay)
            },
            'deductions': {
                'tax': float(record.tax_deduction),
                'other': float(record.other_deductions),
                'total_deductions': float(record.tax_deduction + record.other_deductions)
            },
            'net_pay': float(record.net_pay),
            'generated_date': datetime.now().strftime('%Y-%m-%d')
        }
