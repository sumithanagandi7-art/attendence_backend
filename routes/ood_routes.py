from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models import OOD, Notification
from utils.security import admin_required

ood_bp = Blueprint("ood", __name__, url_prefix="/api/ood")


@ood_bp.route("/apply", methods=["POST"])
@jwt_required()
def apply_ood():
    """Body (JSON): date (YYYY-MM-DD), work_location, purpose"""
    data = request.get_json(force=True)
    try:
        ood_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return jsonify({"error": "date must be provided as YYYY-MM-DD."}), 400

    emp_id = int(get_jwt_identity())
    ood = OOD(employee_id=emp_id, ood_date=ood_date,
              work_location=data.get("work_location", ""), purpose=data.get("purpose", ""))
    db.session.add(ood)
    db.session.commit()
    return jsonify({"message": "OOD request submitted.", "ood": ood.to_dict()}), 201


@ood_bp.route("/my", methods=["GET"])
@jwt_required()
def my_ood():
    emp_id = int(get_jwt_identity())
    requests_ = OOD.query.filter_by(employee_id=emp_id).order_by(OOD.applied_on.desc()).all()
    return jsonify([o.to_dict() for o in requests_]), 200


@ood_bp.route("/<int:ood_id>/status", methods=["PUT"])
@admin_required
def update_ood_status(ood_id):
    """Admin only. Body (JSON): status = approved | rejected"""
    data = request.get_json(force=True)
    status = data.get("status")
    if status not in ("approved", "rejected"):
        return jsonify({"error": "status must be 'approved' or 'rejected'."}), 400

    ood = OOD.query.get_or_404(ood_id)
    ood.status = status
    db.session.add(Notification(employee_id=ood.employee_id, message=f"Your OOD request was {status}."))
    db.session.commit()
    return jsonify({"message": f"OOD {status}.", "ood": ood.to_dict()}), 200
