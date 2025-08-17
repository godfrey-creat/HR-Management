# ============================================================================
# File: app/api/attendance.py
# Attendance Management Blueprint
# ============================================================================

from flask import Blueprint, request, jsonify
from datetime import datetime, date
#from app import db
from app.models.models import Attendance, Employee, db

attendance_bp = Blueprint("attendance", __name__)

# -----------------------------
# Check-in endpoint
# -----------------------------
@attendance_bp.route("/check-in", methods=["POST"])
def check_in():
    data = request.get_json()
    employee_id = data.get("employee_id")
    timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()

    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    record = Attendance.query.filter_by(employee_id=employee.id, date=timestamp.date()).first()
    if record and record.check_in:
        return jsonify({"error": "Already checked in today"}), 400

    if not record:
        record = Attendance(employee_id=employee.id, date=timestamp.date())
        db.session.add(record)

    record.check_in = timestamp
    record.status = "present"
    db.session.commit()

    return jsonify({"message": "Check-in successful", "data": record.to_dict()}), 200


# -----------------------------
# Check-out endpoint
# -----------------------------
@attendance_bp.route("/check-out", methods=["POST"])
def check_out():
    data = request.get_json()
    employee_id = data.get("employee_id")
    timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now()

    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    record = Attendance.query.filter_by(employee_id=employee.id, date=timestamp.date()).first()
    if not record or not record.check_in:
        return jsonify({"error": "Check-in not found"}), 400

    record.check_out = timestamp
    record.calculate_hours_worked()
    db.session.commit()

    return jsonify({"message": "Check-out successful", "data": record.to_dict()}), 200


# -----------------------------
# Attendance report endpoint
# -----------------------------
@attendance_bp.route("/report/<employee_id>", methods=["GET"])
def get_report(employee_id):
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    if not (start_date and end_date):
        return jsonify({"error": "start and end dates required"}), 400

    start_date = datetime.fromisoformat(start_date).date()
    end_date = datetime.fromisoformat(end_date).date()

    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    records = Attendance.query.filter(
        Attendance.employee_id == employee.id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()

    return jsonify({"employee_id": employee_id, "records": [r.to_dict() for r in records]}), 200
