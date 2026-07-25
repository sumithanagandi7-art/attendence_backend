"""
Run this once after the app has created its tables to set up:
  - a default admin login
  - a sample government office work location (Hadalasang high school, as an example)

Usage:
    python seed_data.py
"""
from werkzeug.security import generate_password_hash
from app import create_app
from database import db
from models import Employee, WorkLocation

app = create_app()

with app.app_context():
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
        print("Created default admin -> emp_id: ADMIN001 / password: Admin@123 (CHANGE THIS)")
    else:
        print("Admin already exists, skipping.")

    if not WorkLocation.query.filter_by(name="Government High School, Hadalasang").first():
        loc = WorkLocation(
            name="Government High School, Hadalasang",
            latitude=16.8500,   # sample coordinates -- replace with the real office GPS point
            longitude=75.7000,
            radius_meters=200,
        )
        db.session.add(loc)
        print("Created sample work location: Government High School, Hadalasang")
    else:
        print("Sample location already exists, skipping.")

    db.session.commit()
    print("Seeding complete.")
