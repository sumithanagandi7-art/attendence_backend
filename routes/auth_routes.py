from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

from database import db
from models import Employee
from utils.face_utils import extract_face_encoding, save_uploaded_image

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Public self-registration for new employees.
    Body (JSON): emp_id, name, mobile, password, department, designation

    Security note: every self-registered account is created with
    role="employee" and approval_status="pending" — the client CANNOT set
    its own role or approval status. An admin must approve the account
    (see /api/admin/employees/pending and /api/admin/employees/<id>/approve)
    before the employee can log in.
    """
    data = request.get_json(force=True)
    required = ["emp_id", "name", "mobile", "password"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": f"Missing required fields: {required}"}), 400

    if len(data["password"]) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400

    if Employee.query.filter(
        (Employee.emp_id == data["emp_id"]) | (Employee.mobile == data["mobile"])
    ).first():
        return jsonify({"error": "Employee ID or mobile number already registered."}), 409

    emp = Employee(
        emp_id=data["emp_id"],
        name=data["name"],
        mobile=data["mobile"],
        department=data.get("department"),
        designation=data.get("designation"),
        role="employee",              # self-registration can never create an admin
        approval_status="pending",    # always requires admin approval
        language_pref=data.get("language_pref", "en"),
        password_hash=generate_password_hash(data["password"]),
    )
    db.session.add(emp)
    db.session.commit()
    return jsonify({
        "message": "Registration submitted. An administrator must approve your account before you can log in.",
        "employee": emp.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Body (JSON): emp_id, password"""
    data = request.get_json(force=True)
    emp = Employee.query.filter_by(emp_id=data.get("emp_id")).first()

    if not emp or not check_password_hash(emp.password_hash, data.get("password", "")):
        return jsonify({"error": "Invalid employee ID or password."}), 401

    if emp.approval_status == "pending":
        return jsonify({"error": "Your registration is awaiting admin approval. Please check back later."}), 403
    if emp.approval_status == "rejected":
        return jsonify({"error": "Your registration was rejected. Please contact your administrator."}), 403
    if not emp.is_active:
        return jsonify({"error": "This account has been deactivated. Contact admin."}), 403

    token = create_access_token(
        identity=str(emp.id), additional_claims={"role": emp.role, "emp_id": emp.emp_id}
    )
    return jsonify({"access_token": token, "employee": emp.to_dict()}), 200


@auth_bp.route("/register-face", methods=["POST"])
@jwt_required()
def register_face():
    """
    Enroll a face for the logged-in employee.
    Multipart form-data: image=<file>
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file uploaded (field name must be 'image')."}), 400

    try:
        emp = Employee.query.get(int(get_jwt_identity()))
        uploaded_file = request.files["image"]
        print(f"[FACE-ENROLL] Received file: {uploaded_file.filename}, "
              f"content_type: {uploaded_file.content_type}, "
              f"employee: {emp.emp_id}")

        image_path = save_uploaded_image(uploaded_file, current_app.config["FACE_UPLOAD_DIR"])
        print(f"[FACE-ENROLL] Saved to: {image_path}")

        encoding, error = extract_face_encoding(image_path)
        if error:
            print(f"[FACE-ENROLL] Detection failed: {error}")
            return jsonify({"error": error}), 422

        print(f"[FACE-ENROLL] Face detected successfully, saving encoding")
        emp.set_face_encoding(encoding)
        emp.face_image_path = image_path
        db.session.commit()
        return jsonify({"message": "Face registered successfully."}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Server error during face registration: {str(e)}"}), 500


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    emp = Employee.query.get(int(get_jwt_identity()))
    return jsonify(emp.to_dict()), 200
