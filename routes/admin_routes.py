from datetime import date
from flask import Blueprint, request, jsonify

from database import db
from models import Employee, WorkLocation, EmployeeLocation, Attendance, Leave, OOD
from utils.security import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ---------- Employee management ----------
@admin_bp.route("/employees", methods=["GET"])
@admin_required
def list_employees():
    employees = Employee.query.all()
    return jsonify([e.to_dict() for e in employees]), 200


@admin_bp.route("/employees/pending", methods=["GET"])
@admin_required
def pending_employees():
    """List self-registered employees awaiting admin approval."""
    employees = Employee.query.filter_by(approval_status="pending").order_by(Employee.created_on).all()
    return jsonify([e.to_dict() for e in employees]), 200


@admin_bp.route("/employees/<int:emp_id>/approve", methods=["PUT"])
@admin_required
def approve_employee(emp_id):
    """Body (JSON, optional): status = approved | rejected (defaults to approved)"""
    data = request.get_json(silent=True) or {}
    status = data.get("status", "approved")
    if status not in ("approved", "rejected"):
        return jsonify({"error": "status must be 'approved' or 'rejected'."}), 400

    emp = Employee.query.get_or_404(emp_id)
    emp.approval_status = status
    db.session.commit()
    return jsonify({"message": f"Employee {status}.", "employee": emp.to_dict()}), 200


@admin_bp.route("/employees/<int:emp_id>/deactivate", methods=["PUT"])
@admin_required
def deactivate_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    emp.is_active = False
    db.session.commit()
    return jsonify({"message": "Employee deactivated."}), 200


# ---------- Work location management ----------
@admin_bp.route("/locations", methods=["POST"])
@admin_required
def create_location():
    """Body (JSON): name, latitude, longitude, radius_meters (optional)"""
    data = request.get_json(force=True)
    required = ["name", "latitude", "longitude"]
    if not all(f in data for f in required):
        return jsonify({"error": f"Missing fields: {required}"}), 400

    loc = WorkLocation(name=data["name"], latitude=data["latitude"], longitude=data["longitude"],
                        radius_meters=data.get("radius_meters", 200))
    db.session.add(loc)
    db.session.commit()
    return jsonify({"message": "Location created.", "location": loc.to_dict()}), 201


@admin_bp.route("/locations", methods=["GET"])
@admin_required
def list_locations():
    locs = WorkLocation.query.all()
    return jsonify([l.to_dict() for l in locs]), 200


@admin_bp.route("/employees/<int:emp_id>/assign-location", methods=["POST"])
@admin_required
def assign_location(emp_id):
    """Body (JSON): location_id"""
    data = request.get_json(force=True)
    location_id = data.get("location_id")
    if not location_id:
        return jsonify({"error": "location_id is required."}), 400

    Employee.query.get_or_404(emp_id)
    WorkLocation.query.get_or_404(location_id)

    exists = EmployeeLocation.query.filter_by(employee_id=emp_id, location_id=location_id).first()
    if exists:
        return jsonify({"message": "Already assigned."}), 200

    db.session.add(EmployeeLocation(employee_id=emp_id, location_id=location_id))
    db.session.commit()
    return jsonify({"message": "Location assigned to employee."}), 201


# ---------- Monitoring & approvals ----------
@admin_bp.route("/attendance/all", methods=["GET"])
@admin_required
def all_attendance():
    """Query param: date=YYYY-MM-DD (defaults to today)"""
    day_str = request.args.get("date")
    day = date.fromisoformat(day_str) if day_str else date.today()
    records = Attendance.query.filter_by(att_date=day).all()
    return jsonify([r.to_dict() for r in records]), 200


@admin_bp.route("/leaves/pending", methods=["GET"])
@admin_required
def pending_leaves():
    leaves = Leave.query.filter_by(status="pending").order_by(Leave.applied_on).all()
    return jsonify([l.to_dict() for l in leaves]), 200


@admin_bp.route("/ood/pending", methods=["GET"])
@admin_required
def pending_ood():
    requests_ = OOD.query.filter_by(status="pending").order_by(OOD.applied_on).all()
    return jsonify([o.to_dict() for o in requests_]), 200


@admin_bp.route("/analytics", methods=["GET"])
@admin_required
def analytics():
    """Query param: date=YYYY-MM-DD (defaults to today)"""
    day_str = request.args.get("date")
    day = date.fromisoformat(day_str) if day_str else date.today()

    total_employees = Employee.query.filter_by(is_active=True).count()
    present_today = Attendance.query.filter_by(att_date=day).filter(
        Attendance.check_in_time.isnot(None)).count()

    return jsonify({
        "date": day.isoformat(),
        "total_employees": total_employees,
        "present_today": present_today,
        "absent_today": max(total_employees - present_today, 0),
        "pending_employees": Employee.query.filter_by(approval_status="pending").count(),
        "pending_leaves": Leave.query.filter_by(status="pending").count(),
        "pending_ood": OOD.query.filter_by(status="pending").count(),
    }), 200
