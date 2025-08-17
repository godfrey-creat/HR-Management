# ============================================================================
# File: app/services/notification_service.py
# Notification Service (Email, SMS, etc.)
# ============================================================================

from flask import current_app, render_template_string
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class NotificationService:
    
    @staticmethod
    def send_email(to_email, subject, body, is_html=False):
        """Send email notification"""
        try:
            smtp_server = current_app.config.get('MAIL_SERVER')
            smtp_port = current_app.config.get('MAIL_PORT')
            smtp_username = current_app.config.get('MAIL_USERNAME')
            smtp_password = current_app.config.get('MAIL_PASSWORD')
            
            if not all([smtp_server, smtp_username, smtp_password]):
                current_app.logger.warning("Email configuration not complete")
                return False
            
            msg = MimeMultipart()
            msg['From'] = smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html' if is_html else 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def send_leave_request_notification(leave_request, action='submitted'):
        """Send leave request notification"""
        employee = leave_request.employee
        
        if action == 'submitted':
            subject = f"Leave Request Submitted - {employee.first_name} {employee.last_name}"
            body = f"""
            A new leave request has been submitted:
            
            Employee: {employee.first_name} {employee.last_name}
            Leave Type: {leave_request.leave_type}
            Start Date: {leave_request.start_date}
            End Date: {leave_request.end_date}
            Days: {leave_request.days_requested}
            Reason: {leave_request.reason}
            
            Please review and approve/reject the request.
            """
            # Send to managers/HR
            # This would need manager email lookup logic
            
        elif action == 'approved':
            subject = "Leave Request Approved"
            body = f"""
            Your leave request has been approved:
            
            Leave Type: {leave_request.leave_type}
            Start Date: {leave_request.start_date}
            End Date: {leave_request.end_date}
            Days: {leave_request.days_requested}
            
            Enjoy your time off!
            """
            NotificationService.send_email(employee.email, subject, body)
        
        elif action == 'rejected':
            subject = "Leave Request Rejected"
            body = f"""
            Your leave request has been rejected:
            
            Leave Type: {leave_request.leave_type}
            Start Date: {leave_request.start_date}
            End Date: {leave_request.end_date}
            
            Comments: {leave_request.comments or 'No comments provided'}
            
            Please contact HR for more information.
            """
            NotificationService.send_email(employee.email, subject, body)
    
    @staticmethod
    def send_payslip_notification(employee, payroll_record):
        """Send payslip notification"""
        subject = f"Payslip Generated - {payroll_record.pay_period_start.strftime('%B %Y')}"
        body = f"""
        Dear {employee.first_name},
        
        Your payslip for {payroll_record.pay_period_start.strftime('%B %Y')} has been generated.
        
        Net Pay: ${payroll_record.net_pay:,.2f}
        
        You can view and download your payslip from the employee portal.
        
        Best regards,
        HR Department
        """
        
        NotificationService.send_email(employee.email, subject, body)