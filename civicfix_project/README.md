# CivicFix

A civic-issue reporting platform, matching this workflow exactly:

```
Citizen
  |
  v
Submit Complaint
  |
  v
Department (auto-assigned by category)
  |
  v
Update Complaint Status (Pending -> In Progress -> Resolved)
  |
  v
Admin monitors everything
  |
  v
Admin sends notifications
  |-- Citizen (status updates)
  `-- Department Staff (reminders)
```

Citizens and department staff sign up choosing their role. A citizen's
complaint is auto-routed to the matching department by AI category
detection and flagged as an emergency from the photo/description. Staff
move it through Pending -> In Progress -> Resolved. Admin sees everything
and sends notifications to citizens or department staff. There is no chat
or messaging feature -- notifications and status/update history are the
only communication channel, by design.

```
civicfix_project/
├── backend/     Django REST API + MySQL (accounts, departments, complaints, AI services)
├── frontend/    Plain HTML/CSS/JS client that talks to the API
├── run_windows.bat     one-click start (Windows)
└── run_mac_linux.sh    one-command start (Mac/Linux)
```

---

## 0. Fastest way to run it (recommended)

**First, create the MySQL database** (once):
```bash
mysql -u root -p -e "CREATE DATABASE civicfix CHARACTER SET utf8mb4;"
```
Then check `backend/.env` has the right `DB_USER` / `DB_PASSWORD` for your
MySQL install (defaults to `root` with no password, matching a fresh local
MySQL setup).

**Windows:** double-click `run_windows.bat`. Two terminal windows open
(backend + frontend) and your browser opens automatically.

**Mac/Linux:**
```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```
Leave that terminal open — press `Ctrl+C` to stop both servers.

Either script installs dependencies, runs migrations, seeds departments +
demo accounts, and starts both servers. If migration fails, the script
prints exactly why (almost always: MySQL database doesn't exist yet, or
wrong credentials in `.env`) and how to fix it — including a fallback to
SQLite (`USE_SQLITE=True` in `.env`) if you don't have MySQL installed at all.

If you'd rather run each step yourself, see the manual steps below.

---

## 1. Run the backend manually

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py seed_departments   # required so signup's department dropdown isn't empty
python manage.py seed_demo          # optional: demo admin/department/citizen accounts + 1 sample complaint

python manage.py runserver
```

The API is now live at `http://127.0.0.1:8000/api/`. Django admin: `http://127.0.0.1:8000/admin/`.

`.env` ships pre-configured for MySQL (`USE_SQLITE=False`, database name
`civicfix`, user `root`, no password). Create the database first (see
step 0), or set `USE_SQLITE=True` to skip MySQL entirely. Full API
reference is in `backend/README.md`.

## 2. Run the frontend manually

The frontend is plain static HTML/CSS/JS — no build step. Two ways to run it:

**Option A — just open it:**
Double-click `frontend/index.html` (or open it via `file://` in your browser).

**Option B — serve it (recommended, avoids any local-file quirks):**
```bash
cd frontend
python -m http.server 5500
```
Then visit `http://127.0.0.1:5500/index.html`.

Either way, make sure the **backend is running first** — the frontend calls
`http://127.0.0.1:8000/api` (set at the top of `frontend/assets/js/api.js`;
change `API_BASE` there if your backend runs elsewhere).

---

## 3. How sign-up works

There's no email/OTP step. `register.html` has a role switch:

- **Citizen** — fills in their details and is logged in immediately.
- **Department Staff** — additionally picks which department they belong to,
  from a dropdown populated by `GET /api/departments/` (public endpoint).
  That's why `seed_departments` must be run before anyone signs up as staff.

Admin accounts are **not** self-registerable — an existing admin creates
them from **Admin → Departments & Staff** in the app, or from Django admin.
Admin accounts never appear as a complaint's citizen or a notification's
recipient (enforced in Django admin's dropdowns).

Demo logins from `seed_demo` (if you ran it):

| Role       | Email                        | Password       |
|------------|-------------------------------|----------------|
| Admin      | admin@civicfix.local          | Admin@12345    |
| Department | roads.staff@civicfix.local    | Staff@12345    |
| Citizen    | citizen@civicfix.local        | Citizen@12345  |

---

## 4. Walking through the demo

1. Log in as **citizen** → *Report an Issue* → fill in title/description,
   drop a pin on the map, upload a photo → submit. AI auto-picks a category
   if left blank and flags emergencies from the photo.
2. Log out, sign up (or log in) as **department staff** for that category →
   see the complaint on the dashboard → open it → change status, post a
   progress update.
3. Log in as **admin** → Overview shows citywide stats and any emergencies;
   *Departments & Staff* lets you add departments or provision more staff/admin
   accounts. From Django admin (`/admin/`) you can send a **Notification**
   directly to a citizen (status update) or department staff (reminder).

---

## 5. Testing with Postman

Import `backend/civicfix_postman_collection.json`. It's pre-wired with
`{{base_url}}` and auto-saves `{{access_token}}` / `{{refresh_token}}` from
the Login or Register requests, so every other request in the collection
just works after either one.

---

## 6. Notes for your defense

- **AI categorization** (`backend/ai_services/categorization.py`) is a
  keyword classifier — fast, dependency-free, and swappable for a trained
  NLP model later.
- **AI emergency detection** (`backend/ai_services/image_detection.py`) uses
  image statistics (brightness, edge density, color dominance) as a
  stand-in for a trained computer-vision model — both are isolated behind
  one function each so a real model can drop in without touching anything else.
- **Location** (`backend/ai_services/location_service.py`) reverse-geocodes
  via the free OpenStreetMap Nominatim API.
- **Chatbot** (`backend/ai_services/chatbot.py`) is a rule-based FAQ
  assistant (keyword matching, no paid API) — the floating chat button in
  the bottom-right of every page.
- **Department SLA warnings** — run `python manage.py check_sla` to flag
  complaints a department hasn't acted on within 48h (6h if emergency) and
  notify admins.
- **No messaging/chat between citizens and departments** — by design.
  Communication happens only through complaint status history, department
  updates, and admin-sent notifications.

See `backend/README.md` for the complete API reference and the full
notebook-plan → code mapping table.
