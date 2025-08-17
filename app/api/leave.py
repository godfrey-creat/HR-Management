# routes/leave.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import LeaveManager, LeaveType
from datetime import datetime

leave_bp = Blueprint("leave", __name__, url_prefix="/leave")

# Single shared LeaveManager instance (in-memory for now)
leave_manager = LeaveManager()

@leave_bp.route("/apply", methods=["POST"])
@jwt_required()
def apply_leave():
    data = request.get_json()
    employee_id = get_jwt_identity()
    leave_type = LeaveType(data["leave_type"])
    start_date = datetime.fromisoformat(data["start_date"]).date()
    end_date = datetime.fromisoformat(data["end_date"]).date()
    reason = data.get("reason", "")

    success, result = leave_manager.apply_leave(
        employee_id, leave_type, start_date, end_date, reason, applied_by=employee_id
    )
    if success:
        return jsonify({"message": "Leave application submitted", "application_id": result}), 201
    return jsonify({"error": result}), 400

@leave_bp.route("/approve/<application_id>", methods=["POST"])
@jwt_required()
def approve_leave(application_id):
    manager_id = get_jwt_identity()
    success = leave_manager.approve_leave(application_id, approved_by=manager_id)
    if success:
        return jsonify({"message": "Leave approved"})
    return jsonify({"error": "Approval failed"}), 400

@leave_bp.route("/reject/<application_id>", methods=["POST"])
@jwt_required()
def reject_leave(application_id):
    data = request.get_json()
    manager_id = get_jwt_identity()
    reason = data.get("reason", "No reason provided")
    success = leave_manager.reject_leave(application_id, rejected_by=manager_id, reason=reason)
    if success:
        return jsonify({"message": "Leave rejected"})
    return jsonify({"error": "Rejection failed"}), 400

@leave_bp.route("/cancel/<application_id>", methods=["POST"])
@jwt_required()
def cancel_leave(application_id):
    success = leave_manager.cancel_leave(application_id)
    if success:
        return jsonify({"message": "Leave cancelled"})
    return jsonify({"error": "Cancellation failed"}), 400

@leave_bp.route("/balance", methods=["GET"])
@jwt_required()
def leave_balance():
    employee_id = get_jwt_identity()
    balance = leave_manager.get_leave_balance(employee_id)
    return jsonify(balance)

@leave_bp.route("/applications", methods=["GET"])
@jwt_required()
def my_applications():
    employee_id = get_jwt_identity()
    applications = leave_manager.get_employee_applications(employee_id)
    return jsonify(applications)

@leave_bp.route("/pending", methods=["GET"])
@jwt_required()
def pending_applications():
    pending = leave_manager.get_pending_applications()
    return jsonify(pending)
