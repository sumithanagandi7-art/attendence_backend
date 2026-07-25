from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models import Notification

notification_bp = Blueprint("notification", __name__, url_prefix="/api/notifications")


@notification_bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    emp_id = int(get_jwt_identity())
    notes = Notification.query.filter_by(employee_id=emp_id).order_by(
        Notification.created_on.desc()).limit(50).all()
    return jsonify([n.to_dict() for n in notes]), 200


@notification_bp.route("/<int:note_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(note_id):
    emp_id = int(get_jwt_identity())
    note = Notification.query.filter_by(id=note_id, employee_id=emp_id).first_or_404()
    note.is_read = True
    db.session.commit()
    return jsonify({"message": "Marked as read."}), 200
