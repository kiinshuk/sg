"""
WSGI config for snapgram project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

# Add project directory to Python path
path = '/home/kiinshuk/sg'
if path not in sys.path:
    sys.path.insert(0, path)

# Environment variables for PythonAnywhere
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snapgram.settings')
os.environ['SECRET_KEY'] = 'YOUR-SECRET-KEY-HERE'
os.environ['DEBUG'] = 'False'
os.environ['MYSQL_DB'] = '1'
os.environ['MYSQL_NAME'] = 'kiinshuk$snapgram'
os.environ['MYSQL_USER'] = 'kiinshuk'
os.environ['MYSQL_PASSWORD'] = 'YOUR-MYSQL-PASSWORD'
os.environ['MYSQL_HOST'] = 'mysql.pythonanywhere-services.com'
os.environ['MYSQL_PORT'] = '3306'
os.environ['CLOUDINARY_CLOUD_NAME'] = 'YOUR-CLOUD-NAME'
os.environ['CLOUDINARY_API_KEY'] = 'YOUR-API-KEY'
os.environ['CLOUDINARY_API_SECRET'] = 'YOUR-API-SECRET'

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
