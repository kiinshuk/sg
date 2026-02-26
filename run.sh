#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Snapgram..."
echo "Open http://127.0.0.1:8000 in your browser"
echo "Admin panel: http://127.0.0.1:8000/admin (admin / admin123)"
venv/bin/python manage.py runserver
