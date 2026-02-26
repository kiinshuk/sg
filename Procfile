web: python manage.py migrate && python manage.py create_admin && gunicorn snapgram.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 120
