import json
from datetime import datetime, date
from database import db


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="employee")  # employee | admin
    approval_status = db.Column(db.String(20), default="pending")  # pending | approved | rejected
    language_pref = db.Column(db.String(20), default="en")  # en | kn | hi
    face_encoding = db.Column(db.Text)  # JSON-serialized 128-d face encoding
    face_image_path = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    attendances = db.relationship("Attendance", backref="employee", lazy=True)
    leaves = db.relationship("Leave", backref="employee", lazy=True, foreign_keys="Leave.employee_id")
    oods = db.relationship("OOD", backref="employee", lazy=True)
    tickets = db.relationship("SupportTicket", backref="employee", lazy=True)
    notifications = db.relationship("Notification", backref="employee", lazy=True)

    def set_face_encoding(self, encoding_list):
        self.face_encoding = json.dumps(encoding_list)

    def get_face_encoding(self):
        return json.loads(self.face_encoding) if self.face_encoding else None

    def to_dict(self):
        return {
            "id": self.id,
            "emp_id": self.emp_id,
            "name": self.name,
            "mobile": self.mobile,
            "department": self.department,
            "designation": self.designation,
            "role": self.role,
            "approval_status": self.approval_status,
            "language_pref": self.language_pref,
            "face_registered": bool(self.face_encoding),
            "is_active": self.is_active,
        }


class WorkLocation(db.Model):
    __tablename__ = "work_locations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius_meters = db.Column(db.Integer, default=200)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "radius_meters": self.radius_meters,
        }


class EmployeeLocation(db.Model):
    """Many-to-many: employees can be authorized for multiple locations."""
    __tablename__ = "employee_locations"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("work_locations.id"), nullable=False)

    employee = db.relationship("Employee")
    location = db.relationship("WorkLocation")


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    att_date = db.Column(db.Date, default=date.today, index=True)

    check_in_time = db.Column(db.DateTime)
    check_in_lat = db.Column(db.Float)
    check_in_lng = db.Column(db.Float)
    check_in_location_id = db.Column(db.Integer, db.ForeignKey("work_locations.id"))
    check_in_face_score = db.Column(db.Float)

    check_out_time = db.Column(db.DateTime)
    check_out_lat = db.Column(db.Float)
    check_out_lng = db.Column(db.Float)
    check_out_location_id = db.Column(db.Integer, db.ForeignKey("work_locations.id"))
    check_out_face_score = db.Column(db.Float)

    working_hours = db.Column(db.Float)
    status = db.Column(db.String(20), default="present")  # present | half_day | absent

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "date": self.att_date.isoformat(),
            "check_in_time": self.check_in_time.isoformat() if self.check_in_time else None,
            "check_out_time": self.check_out_time.isoformat() if self.check_out_time else None,
            "working_hours": self.working_hours,
            "status": self.status,
        }


class Leave(db.Model):
    __tablename__ = "leaves"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    leave_type = db.Column(db.String(30))  # casual | sick | earned | emergency | other
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")  # pending | approved | rejected
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "leave_type": self.leave_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "reason": self.reason,
            "status": self.status,
            "applied_on": self.applied_on.isoformat(),
        }


class OOD(db.Model):
    __tablename__ = "ood_requests"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    ood_date = db.Column(db.Date, nullable=False)
    work_location = db.Column(db.String(200))
    purpose = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "date": self.ood_date.isoformat(),
            "work_location": self.work_location,
            "purpose": self.purpose,
            "status": self.status,
        }


class SupportTicket(db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    subject = db.Column(db.String(200))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="open")  # open | in_progress | resolved
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "created_on": self.created_on.isoformat(),
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "is_read": self.is_read,
            "created_on": self.created_on.isoformat(),
        }
