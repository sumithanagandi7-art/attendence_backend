from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash

from config import Config
from database import db

from routes.auth_routes import auth_bp
from routes.attendance_routes import attendance_bp
from routes.leave_routes import leave_bp
from routes.ood_routes import ood_bp
from routes.report_routes import report_bp
from routes.support_routes import support_bp
from routes.admin_routes import admin_bp
from routes.notification_routes import notification_bp


def _auto_seed():
    """Create default admin and sample location if they don't exist yet.
    Runs on every startup but is idempotent (skips if data already present)."""
    from models import Employee, WorkLocation

    if not Employee.query.filter_by(emp_id="ADMIN001").first():
        admin = Employee(
            emp_id="ADMIN001",
            name="System Administrator",
            mobile="9999999999",
            department="IT Cell",
            designation="Administrator",
            role="admin",
            approval_status="approved",
            password_hash=generate_password_hash("Admin@123"),
        )
        db.session.add(admin)
        print("AUTO-SEED: Created default admin -> ADMIN001 / Admin@123")

    if not WorkLocation.query.filter_by(name="Government High School, Hadalasang").first():
        loc = WorkLocation(
            name="Government High School, Hadalasang",
            latitude=16.8500,
            longitude=75.7000,
            radius_meters=200,
        )
        db.session.add(loc)
        print("AUTO-SEED: Created sample work location")

    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    JWTManager(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(ood_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notification_bp)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "SmartGov Attendance API"}), 200

    with app.app_context():
        db.create_all()  # creates all DBMS tables if they don't already exist
        _auto_seed()     # seed default admin & location if not present

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
