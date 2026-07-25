from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models import Leave, Notification
from utils.security import admin_required

leave_bp = Blueprint("leave", __name__, url_prefix="/api/leave")

VALID_TYPES = {"casual", "sick", "earned", "emergency", "other"}


@leave_bp.route("/apply", methods=["POST"])
@jwt_required()
def apply_leave():
    """Body (JSON): leave_type, start_date (YYYY-MM-DD), end_date, reason"""
    data = request.get_json(force=True)
    leave_type = data.get("leave_type", "other")
    if leave_type not in VALID_TYPES:
        return jsonify({"error": f"leave_type must be one of {sorted(VALID_TYPES)}"}), 400

    try:
        start = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return jsonify({"error": "start_date and end_date must be provided as YYYY-MM-DD."}), 400

    if end < start:
        return jsonify({"error": "end_date cannot be before start_date."}), 400

    emp_id = int(get_jwt_identity())
    leave = Leave(employee_id=emp_id, leave_type=leave_type, start_date=start,
                  end_date=end, reason=data.get("reason", ""))
    db.session.add(leave)
    db.session.commit()
    return jsonify({"message": "Leave application submitted.", "leave": leave.to_dict()}), 201


@leave_bp.route("/my", methods=["GET"])
@jwt_required()
def my_leaves():
    emp_id = int(get_jwt_identity())
    leaves = Leave.query.filter_by(employee_id=emp_id).order_by(Leave.applied_on.desc()).all()
    return jsonify([l.to_dict() for l in leaves]), 200


@leave_bp.route("/<int:leave_id>/status", methods=["PUT"])
@admin_required
def update_leave_status(leave_id):
    """Admin only. Body (JSON): status = approved | rejected"""
    data = request.get_json(force=True)
    status = data.get("status")
    if status not in ("approved", "rejected"):
        return jsonify({"error": "status must be 'approved' or 'rejected'."}), 400

    leave = Leave.query.get_or_404(leave_id)
    leave.status = status
    db.session.add(Notification(employee_id=leave.employee_id,
                                 message=f"Your {leave.leave_type} leave request was {status}."))
    db.session.commit()
    return jsonify({"message": f"Leave {status}.", "leave": leave.to_dict()}), 200
