#!/bin/bash
# CivicFix - one-command start for Mac/Linux
# Usage: chmod +x run_mac_linux.sh && ./run_mac_linux.sh
set -e
cd "$(dirname "$0")"

echo "==> Setting up backend..."
cd backend
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt --quiet

echo "==> Running database migrations (MySQL by default)..."
if ! python manage.py migrate; then
  echo ""
  echo "!! Migration failed. This is almost always because the MySQL database"
  echo "   doesn't exist yet, or the credentials in backend/.env are wrong."
  echo ""
  echo "   Fix option 1 (create the MySQL database):"
  echo "     mysql -u root -p -e \"CREATE DATABASE civicfix CHARACTER SET utf8mb4;\""
  echo "     then check DB_USER/DB_PASSWORD/DB_HOST/DB_PORT in backend/.env"
  echo ""
  echo "   Fix option 2 (skip MySQL entirely for this demo):"
  echo "     open backend/.env and set USE_SQLITE=True, then re-run this script"
  echo ""
  exit 1
fi

python manage.py seed_departments
python manage.py seed_demo

echo "==> Starting backend on http://127.0.0.1:8000 ..."
python manage.py runserver > ../backend.log 2>&1 &
BACKEND_PID=$!

cd ../frontend
echo "==> Starting frontend on http://127.0.0.1:5500 ..."
python3 -m http.server 5500 > ../frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 2
echo ""
echo "CivicFix is running:"
echo "  Backend  -> http://127.0.0.1:8000/api"
echo "  Frontend -> http://127.0.0.1:5500/index.html"
echo ""
echo "Opening it in your browser..."
( command -v open >/dev/null && open http://127.0.0.1:5500/index.html ) || \
( command -v xdg-open >/dev/null && xdg-open http://127.0.0.1:5500/index.html ) || \
echo "Open http://127.0.0.1:5500/index.html manually."

echo ""
echo "Press Ctrl+C to stop both servers."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
