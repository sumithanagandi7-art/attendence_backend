# SmartGov Attendance — Backend (Flask + DBMS)

AI-powered, location-aware attendance & workforce management backend for
government employees: GPS geofencing, face-recognition check-in/out, leave
management, Out-of-Office-Duty (OOD) requests, reports, support tickets, and
an admin dashboard API.

**Stack:** Python 3.10+ · Flask · SQLAlchemy (DBMS: SQLite by default, or
PostgreSQL/MySQL) · Flask-JWT-Extended · `face_recognition` (dlib) · `geopy`

---

## 1. Project structure

```
smartgov/
├── app.py                  # Flask app factory & entrypoint
├── config.py                # DBMS URI, JWT secret, face/geofence settings
├── database.py               # SQLAlchemy instance
├── models.py                  # DBMS tables: Employee, Attendance, Leave, OOD, ...
├── seed_data.py                # Creates a default admin + sample location
├── requirements.txt
├── routes/
│   ├── auth_routes.py         # register / login / face enrollment
│   ├── attendance_routes.py   # check-in / check-out (face + GPS)
│   ├── leave_routes.py
│   ├── ood_routes.py
│   ├── report_routes.py
│   ├── support_routes.py
│   ├── notification_routes.py
│   └── admin_routes.py
└── utils/
    ├── face_utils.py         # face encoding + comparison
    ├── geo_utils.py          # haversine distance / geofence check
    └── security.py           # admin_required decorator
```

## 2. Prerequisites

1. **Python 3.10+**
2. **A C++ build toolchain + CMake**, required to build `dlib` (the engine
   behind the `face_recognition` library):
   - **Ubuntu/Debian:** `sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev`
   - **macOS:** `xcode-select --install` then `brew install cmake`
   - **Windows:** install "Desktop development with C++" via Visual Studio
     Build Tools, and CMake from cmake.org
3. (Optional) A running **PostgreSQL** or **MySQL** server, if you don't
   want to use the default SQLite file database.

## 3. Install

```bash
cd smartgov
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

> If `dlib`/`face-recognition` fails to build, it is almost always a missing
> CMake/compiler — install the prerequisites in step 2 and retry.

## 4. Configure the database

**Option A — SQLite (default, zero setup):** do nothing. A file
`smartgov.db` is created automatically in the project folder on first run.

**Option B — PostgreSQL / MySQL:**

```bash
# PostgreSQL example
export DATABASE_URL="postgresql+psycopg2://smartgov_user:password@localhost:5432/smartgov"
pip install psycopg2-binary

# MySQL example
export DATABASE_URL="mysql+pymysql://smartgov_user:password@localhost:3306/smartgov"
pip install pymysql
```
(On Windows use `set DATABASE_URL=...` or `$env:DATABASE_URL="..."` in PowerShell.)

Also set a real secret key in production:
```bash
export JWT_SECRET_KEY="a-long-random-string"
```

## 5. Run the server

```bash
python app.py
```
This starts the API at `http://localhost:5000` and auto-creates all DBMS
tables (`db.create_all()` in `app.py`).

## 6. Seed a default admin + sample office location

In a second terminal (with the venv activated):
```bash
python seed_data.py
```
This creates:
- Admin login → `emp_id: ADMIN001`, `password: Admin@123` (**change this immediately**)
- A sample work location "Government High School, Hadalasang" — edit the
  latitude/longitude in `seed_data.py` to your real office coordinates
  before running, or add real locations via the admin API (step 7).

## 7. Try it out (example flow with `curl`)

```bash
# 1. Register an employee
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"emp_id":"EMP001","name":"Ravi Kumar","mobile":"9000000001","password":"Pass@123","department":"Education"}'

# 2. Log in (employee or admin)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"emp_id":"EMP001","password":"Pass@123"}'
# -> copy the "access_token" from the response

TOKEN="paste-token-here"

# 3. Enroll face (upload a clear, single-face photo)
curl -X POST http://localhost:5000/api/auth/register-face \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/face.jpg"

# 4. Admin: assign the employee to a work location
ADMIN_TOKEN="paste-admin-token-here"
curl -X POST http://localhost:5000/api/admin/employees/1/assign-location \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"location_id":1}'

# 5. Check in (photo + current GPS coordinates)
curl -X POST http://localhost:5000/api/attendance/checkin \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/live_selfie.jpg" \
  -F "latitude=16.8501" -F "longitude=75.7002"

# 6. Check out
curl -X POST http://localhost:5000/api/attendance/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/live_selfie.jpg" \
  -F "latitude=16.8501" -F "longitude=75.7002"

# 7. Apply for leave
curl -X POST http://localhost:5000/api/leave/apply \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"leave_type":"casual","start_date":"2026-07-25","end_date":"2026-07-26","reason":"Family function"}'

# 8. Monthly report
curl http://localhost:5000/api/reports/monthly?month=2026-07 -H "Authorization: Bearer $TOKEN"
```

## 8. API summary

| Area          | Endpoint                                        | Method |
|---------------|--------------------------------------------------|--------|
| Auth          | `/api/auth/register`                             | POST   |
|               | `/api/auth/login`                                 | POST   |
|               | `/api/auth/register-face`                         | POST   |
| Attendance    | `/api/attendance/checkin`                          | POST   |
|               | `/api/attendance/checkout`                          | POST   |
|               | `/api/attendance/today`, `/history`                | GET    |
| Leave         | `/api/leave/apply`, `/my`                          | POST/GET |
|               | `/api/leave/<id>/status` (admin)                    | PUT    |
| OOD           | `/api/ood/apply`, `/my`                            | POST/GET |
|               | `/api/ood/<id>/status` (admin)                      | PUT    |
| Reports       | `/api/reports/daily`, `/monthly`, `/calendar`        | GET    |
| Support       | `/api/support/faq`, `/ticket`, `/my`                | GET/POST |
| Notifications | `/api/notifications`                                | GET    |
| Admin         | `/api/admin/employees`, `/locations`, `/analytics`, `/attendance/all`, `/leaves/pending`, `/ood/pending` | GET/POST |

## 9. Design notes matching the problem statement

- **Face recognition:** `face_recognition` extracts a 128-d embedding per
  face; check-in/out compares the live photo's embedding against the
  employee's enrolled embedding using Euclidean distance
  (`FACE_MATCH_TOLERANCE` in `config.py`, default 0.5).
- **GPS geofencing:** `geopy.distance.geodesic` computes the distance between
  the employee's live GPS point and every work location they're authorized
  for; a match requires being inside that location's `radius_meters`.
- **Multiple authorized locations per employee** are modeled via the
  `employee_locations` join table (supports field staff with several sites).
- **Role-based access control:** JWT carries a `role` claim; `admin_required`
  gates admin-only endpoints (approvals, employee/location management,
  analytics).
- **Offline caching / large-scale rollout:** not implemented in this backend
  (mobile-side concern) — the API is stateless and horizontally scalable
  behind a load balancer; swap SQLite for PostgreSQL/MySQL for multi-user,
  multi-department production use, as shown in step 4.
- **Multi-language/accessibility (Kannada, Hindi, etc.):** `language_pref` is
  stored per employee; actual localized UI strings belong in the mobile
  front-end, not this backend.

## 10. Production hardening checklist (not included by default)

- Restrict `/api/auth/register` to admins only (currently open for demo ease).
- Enforce HTTPS everywhere (JWTs and face images must not travel over plain HTTP).
- Add rate limiting on login/check-in endpoints.
- Add GPS spoofing detection (e.g., mock-location flags from the mobile SDK).
- Add automated DB backups and a proper migration tool (Flask-Migrate/Alembic)
  instead of `db.create_all()`.
#   a t t e n d e n c e _ b a c k e n d  
 