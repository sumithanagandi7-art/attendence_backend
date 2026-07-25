from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models import Attendance

report_bp = Blueprint("report", __name__, url_prefix="/api/reports")


@report_bp.route("/daily", methods=["GET"])
@jwt_required()
def daily_report():
    """Query param: date=YYYY-MM-DD (defaults to today)"""
    emp_id = int(get_jwt_identity())
    day_str = request.args.get("date")
    day = date.fromisoformat(day_str) if day_str else date.today()

    record = Attendance.query.filter_by(employee_id=emp_id, att_date=day).first()
    return jsonify(record.to_dict() if record else {"date": day.isoformat(), "status": "absent"}), 200


@report_bp.route("/monthly", methods=["GET"])
@jwt_required()
def monthly_report():
    """Query param: month=YYYY-MM (defaults to current month)"""
    emp_id = int(get_jwt_identity())
    month_str = request.args.get("month", date.today().strftime("%Y-%m"))
    year, mon = map(int, month_str.split("-"))

    records = Attendance.query.filter(
        Attendance.employee_id == emp_id,
        db.extract("year", Attendance.att_date) == year,
        db.extract("month", Attendance.att_date) == mon,
    ).order_by(Attendance.att_date).all()

    summary = {
        "month": month_str,
        "present_days": sum(1 for r in records if r.status == "present"),
        "half_days": sum(1 for r in records if r.status == "half_day"),
        "total_hours": round(sum(r.working_hours or 0 for r in records), 2),
        "days": [r.to_dict() for r in records],
    }
    return jsonify(summary), 200


@report_bp.route("/calendar", methods=["GET"])
@jwt_required()
def calendar_view():
    """
    Returns a date -> status map for a given month, suitable for rendering
    a calendar widget in the mobile app.
    Query param: month=YYYY-MM
    """
    emp_id = int(get_jwt_identity())
    month_str = request.args.get("month", date.today().strftime("%Y-%m"))
    year, mon = map(int, month_str.split("-"))

    records = Attendance.query.filter(
        Attendance.employee_id == emp_id,
        db.extract("year", Attendance.att_date) == year,
        db.extract("month", Attendance.att_date) == mon,
    ).all()

    calendar = {r.att_date.isoformat(): r.status for r in records}
    return jsonify(calendar), 200
