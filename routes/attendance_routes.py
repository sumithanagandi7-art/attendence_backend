from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models import Employee, Attendance, EmployeeLocation, Notification
from utils.face_utils import extract_face_encoding, compare_faces, save_uploaded_image
from utils.geo_utils import find_matching_location

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")


def _authorized_locations(employee_id):
    links = EmployeeLocation.query.filter_by(employee_id=employee_id).all()
    return [link.location for link in links]


def _verify_face_and_location(emp, request):
    """Shared verification logic for check-in and check-out."""
    if "image" not in request.files:
        return None, None, None, ({"error": "No image file uploaded (field name 'image')."}, 400)

    lat = request.form.get("latitude", type=float)
    lng = request.form.get("longitude", type=float)
    if lat is None or lng is None:
        return None, None, None, ({"error": "latitude and longitude are required."}, 400)

    if not emp.face_encoding:
        return None, None, None, ({"error": "No face enrolled for this employee. Use /api/auth/register-face first."}, 422)

    image_path = save_uploaded_image(request.files["image"], current_app.config["FACE_UPLOAD_DIR"])
    candidate_encoding, error = extract_face_encoding(image_path)
    if error:
        return None, None, None, ({"error": error}, 422)

    is_match, distance = compare_faces(
        emp.get_face_encoding(), candidate_encoding, current_app.config["FACE_MATCH_TOLERANCE"]
    )
    if not is_match:
        return None, None, None, ({"error": "Face verification failed. Face does not match registered profile.",
                                    "distance": distance}, 401)

    locations = _authorized_locations(emp.id)
    if not locations:
        return None, None, None, ({"error": "No authorized work location assigned to this employee."}, 422)

    matched_location, dist_m = find_matching_location(lat, lng, locations)
    if not matched_location:
        return None, None, None, ({"error": "You are not within any authorized work location's geofence."}, 403)

    return (lat, lng, matched_location, distance), None, None, None


@attendance_bp.route("/checkin", methods=["POST"])
@jwt_required()
def check_in():
    """
    Multipart form-data: image=<file>, latitude=<float>, longitude=<float>
    """
    emp = Employee.query.get(int(get_jwt_identity()))
    result, _, _, err = _verify_face_and_location(emp, request)
    if err:
        body, status = err
        return jsonify(body), status
    lat, lng, location, face_distance = result

    today = date.today()
    existing = Attendance.query.filter_by(employee_id=emp.id, att_date=today).first()
    if existing and existing.check_in_time:
        return jsonify({"error": "Already checked in today."}), 409

    record = existing or Attendance(employee_id=emp.id, att_date=today)
    record.check_in_time = datetime.utcnow()
    record.check_in_lat, record.check_in_lng = lat, lng
    record.check_in_location_id = location.id
    record.check_in_face_score = face_distance
    record.status = "present"

    db.session.add(record)
    db.session.add(Notification(employee_id=emp.id,
                                 message=f"Checked in at {location.name} at {record.check_in_time.strftime('%H:%M')}."))
    db.session.commit()
    return jsonify({"message": "Checked in successfully.", "attendance": record.to_dict()}), 200


@attendance_bp.route("/checkout", methods=["POST"])
@jwt_required()
def check_out():
    emp = Employee.query.get(int(get_jwt_identity()))
    result, _, _, err = _verify_face_and_location(emp, request)
    if err:
        body, status = err
        return jsonify(body), status
    lat, lng, location, face_distance = result

    today = date.today()
    record = Attendance.query.filter_by(employee_id=emp.id, att_date=today).first()
    if not record or not record.check_in_time:
        return jsonify({"error": "You must check in before checking out."}), 409
    if record.check_out_time:
        return jsonify({"error": "Already checked out today."}), 409

    record.check_out_time = datetime.utcnow()
    record.check_out_lat, record.check_out_lng = lat, lng
    record.check_out_location_id = location.id
    record.check_out_face_score = face_distance

    delta = record.check_out_time - record.check_in_time
    record.working_hours = round(delta.total_seconds() / 3600, 2)
    if record.working_hours < 4:
        record.status = "half_day"

    db.session.add(Notification(employee_id=emp.id,
                                 message=f"Checked out at {location.name}. Total hours: {record.working_hours}."))
    db.session.commit()
    return jsonify({"message": "Checked out successfully.", "attendance": record.to_dict()}), 200


@attendance_bp.route("/today", methods=["GET"])
@jwt_required()
def today_attendance():
    emp_id = int(get_jwt_identity())
    record = Attendance.query.filter_by(employee_id=emp_id, att_date=date.today()).first()
    return jsonify(record.to_dict() if record else {}), 200


@attendance_bp.route("/history", methods=["GET"])
@jwt_required()
def history():
    """Query params: month=YYYY-MM (optional)"""
    emp_id = int(get_jwt_identity())
    query = Attendance.query.filter_by(employee_id=emp_id)

    month = request.args.get("month")
    if month:
        year, mon = map(int, month.split("-"))
        query = query.filter(db.extract("year", Attendance.att_date) == year,
                              db.extract("month", Attendance.att_date) == mon)

    records = query.order_by(Attendance.att_date.desc()).all()
    return jsonify([r.to_dict() for r in records]), 200
