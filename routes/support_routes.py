from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models import SupportTicket
from utils.security import admin_required

support_bp = Blueprint("support", __name__, url_prefix="/api/support")

FAQ = [
    {"q": "I checked in but the app says location not authorized.",
     "a": "Make sure GPS/location services are turned on and you are physically within "
          "200 meters of your assigned office. Contact your admin if your work location "
          "needs to be updated."},
    {"q": "Face verification keeps failing.",
     "a": "Re-register your face in good lighting, facing the camera directly, with no mask "
          "or sunglasses. Go to Profile > Re-register Face."},
    {"q": "How do I apply for leave?",
     "a": "Go to Leave > Apply, choose the leave type, dates, and reason, then submit. "
          "You'll get a notification once your admin reviews it."},
    {"q": "What is an OOD request?",
     "a": "Out of Office Duty (OOD) is used when you need to work from a location other "
          "than your assigned office for official duty."},
]


@support_bp.route("/faq", methods=["GET"])
def faq():
    return jsonify(FAQ), 200


@support_bp.route("/ticket", methods=["POST"])
@jwt_required()
def create_ticket():
    """Body (JSON): subject, description"""
    data = request.get_json(force=True)
    if not data.get("subject"):
        return jsonify({"error": "subject is required."}), 400

    emp_id = int(get_jwt_identity())
    ticket = SupportTicket(employee_id=emp_id, subject=data["subject"],
                            description=data.get("description", ""))
    db.session.add(ticket)
    db.session.commit()
    return jsonify({"message": "Support ticket raised.", "ticket": ticket.to_dict()}), 201


@support_bp.route("/my", methods=["GET"])
@jwt_required()
def my_tickets():
    emp_id = int(get_jwt_identity())
    tickets = SupportTicket.query.filter_by(employee_id=emp_id).order_by(
        SupportTicket.created_on.desc()).all()
    return jsonify([t.to_dict() for t in tickets]), 200


@support_bp.route("/<int:ticket_id>/status", methods=["PUT"])
@admin_required
def update_ticket_status(ticket_id):
    """Admin only. Body (JSON): status = open | in_progress | resolved"""
    data = request.get_json(force=True)
    status = data.get("status")
    if status not in ("open", "in_progress", "resolved"):
        return jsonify({"error": "Invalid status."}), 400

    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.status = status
    db.session.commit()
    return jsonify({"message": "Ticket updated.", "ticket": ticket.to_dict()}), 200
