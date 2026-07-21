# CivicFix — Backend

A civic-issue reporting platform. Citizens report problems (road damage,
water leakage, garbage, street lights, drainage, etc.) with a photo and
location; AI auto-categorizes the report and flags likely emergencies from
the photo; the right department gets notified, tracks the complaint through
Pending → In Progress → Resolved, with the admin sending notifications to citizens (status updates) and department staff (reminders).

Built with **Django + Django REST Framework**, JWT auth, MySQL (or SQLite
for a zero-config demo), and free OpenStreetMap geocoding.

---

## 1. Quick start (fastest way to a working demo)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Create the MySQL database once (skip if you're using SQLite instead -- see section 2):
mysql -u root -p -e "CREATE DATABASE civicfix CHARACTER SET utf8mb4;"

# .env is already included, pre-configured for MySQL (USE_SQLITE=False, user root, no password)
python manage.py migrate

python manage.py seed_departments   # required so the signup dropdown for department staff isn't empty
python manage.py seed_demo          # creates demo admin/staff/citizen accounts + 1 sample complaint

python manage.py runserver
```

The API is now running at `http://127.0.0.1:8000/`.

Demo logins created by `seed_demo`:

| Role       | Email                        | Password       |
|------------|-------------------------------|----------------|
| Admin      | admin@civicfix.local          | Admin@12345    |
| Department | roads.staff@civicfix.local    | Staff@12345    |
| Citizen    | citizen@civicfix.local        | Citizen@12345  |

Django admin panel: `http://127.0.0.1:8000/admin/` (log in with the admin account above).

---

## 2. Falling back to SQLite (if you don't have MySQL installed)

MySQL is the default, but if you don't have a MySQL server available, you
can skip it entirely:

1. Edit `.env` and set:
   ```
   USE_SQLITE=True
   ```
2. `python manage.py migrate` then `python manage.py seed_departments` and `python manage.py seed_demo`.

That's it — no other settings need to change, and everything else in this
README works identically either way.

If you do use MySQL and `pip install mysqlclient` fails (common on
Windows/Mac), install its platform prerequisite first — e.g.
`brew install mysql-client` on Mac, or the Microsoft C++ Build Tools on
Windows — then retry. `database/schema.sql` documents the resulting table
shapes for reference/diagrams; Django's migrations create the real tables,
so you never need to run that file by hand.

---

## 3. How the notebook plan maps to this code

| Your notes | Where it lives |
|---|---|
| Login/register, choosing Citizen or Department role at signup | `accounts` app — `register/` (role + department fields), `login/` |
| Complaint form: title, description, category, photo | `complaints` app — `ComplaintCreateSerializer` |
| Categories: Road damage, Water leakage, Garbage, Street light, Drainage, Others | `Department.Category` / `Complaint.Category` choices |
| "AI should detect it and mark it as emergency" | `ai_services/image_detection.py` → `detect_emergency()` |
| Auto-categorize if left blank | `ai_services/categorization.py` → `categorize()` |
| OpenAPI map integration for location | `ai_services/location_service.py` → free OpenStreetMap Nominatim reverse-geocoding |
| Track status: Pending / In Progress / Resolved | `Complaint.status` + `ComplaintStatusHistory` audit trail |
| "Receives updates" page | `ComplaintUpdate` model + `/complaints/<id>/updates/` |
| Admin can view/warn/manage departments | `accounts` staff endpoints (admin-only) + `departments` app |
| Admin sends notifications to Citizens (status) or Department Staff (reminders) | `Notification` model — created via Django admin, listed via `/complaints/notifications/` |
| Department SLA / "isn't working" warning, shorter during emergency | `complaints check_sla` management command (48h normal / 6h emergency) |
| Tools: Django, MySQL, OpenMapAPI, HTML/CSS/JS frontend | Matches exactly — this repo is the backend half; plug any frontend into these JSON endpoints |

**Being upfront about the AI pieces for your defense:** true image-based
emergency detection and NLP categorization need a trained model + labeled
data, which is out of scope to train from scratch overnight. This project
ships working, swappable implementations — `categorization.py` uses keyword
matching, `image_detection.py` uses image statistics (brightness, edge
density, color dominance) as a stand-in heuristic — both isolated behind a
single function so you can honestly explain "here's the interface; a real
model plugs in here" if asked, without any other code changing.

---

## 4. Full API reference

Base URL: `/api/`

### Auth (`/api/auth/`)
| Method | Endpoint | Who | Description |
|---|---|---|---|
| POST | `register/` | anyone | Self sign-up. `{email, password, first_name, last_name, phone, role, department}` — `role` is `citizen` or `department`; `department` (an ID) is required only when `role="department"`. Logs the account straight in and returns `{access, refresh, user}`, same shape as `/login/`. |
| POST | `login/` | anyone | `{email, password}` → `{access, refresh, user}` |
| POST | `token/refresh/` | anyone | `{refresh}` → new access token |
| GET/PATCH | `me/` | authenticated | View/update your own profile |
| POST | `change-password/` | authenticated | `{old_password, new_password}` |
| GET/POST | `staff/` | admin | List/create department staff or admin accounts |
| GET/PATCH/DELETE | `staff/<id>/` | admin | Manage one staff account |
| GET | `citizens/` | admin | List all citizen accounts |

### Departments (`/api/departments/`)
| Method | Endpoint | Who | Description |
|---|---|---|---|
| GET | `` | authenticated | List departments |
| POST | `` | admin | Create a department |
| GET/PATCH/DELETE | `<id>/` | admin (write) | Manage a department |

### Complaints (`/api/complaints/`)
| Method | Endpoint | Who | Description |
|---|---|---|---|
| GET | `` | authenticated | Role-scoped list. Filters: `?status=&category=&is_emergency=&department=` |
| POST | `` | citizen | Submit a complaint (multipart form for photo). `category` optional — AI fills it in if blank. |
| GET | `<id>/` | participant | Full detail incl. status history + updates |
| PATCH | `<id>/status/` | department/admin | `{status, note}` — pending/in_progress/resolved |
| GET/POST | `<id>/updates/` | participant | Progress-update thread (post = staff/admin only) |
| GET | `stats/` | authenticated | Role-scoped dashboard counts |
| GET | `notifications/` | authenticated | Your notifications |
| POST | `notifications/<id>/read/` | authenticated | Mark one notification read |

All authenticated requests need: `Authorization: Bearer <access_token>`.

### Chatbot (`/api/chatbot/`)
| Method | Endpoint | Who | Description |
|---|---|---|---|
| POST | `ask/` | anyone | `{message}` → `{reply}`. Rule-based FAQ assistant, no login required. |

---

## 5. Testing with Postman

Import `civicfix_postman_collection.json` (included in this delivery). It's
pre-wired with a collection variable `{{base_url}}` (defaults to
`http://127.0.0.1:8000/api`) and `{{access_token}}` / `{{refresh_token}}`
that auto-populate from the Login request's response, so once you log in
every other request in the collection just works.

---

## 6. Background jobs for the demo

```bash
# Warns admins about complaints a department hasn't acted on within SLA
python manage.py check_sla
```
Run this manually before your defense to show the "department isn't
working" warning notification in action, or wire it to a cron job / Windows
Task Scheduler for a live deployment.

---

## 7. Project structure

```
backend/
├── civicfix/          # project settings, root urls
├── accounts/          # custom User (citizen/department/admin), role-choice signup, JWT
├── departments/        # Department model + category routing + seed command
├── complaints/         # Complaint, status history, updates, notifications
├── ai_services/         # categorization.py, image_detection.py, location_service.py, chatbot.py
├── database/schema.sql  # reference MySQL schema (for diagrams/defense)
├── requirements.txt
├── .env.example / .env
└── manage.py
```
