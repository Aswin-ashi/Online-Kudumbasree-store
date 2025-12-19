"""
WSGI config for store project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

# import os

# from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'store.settings')

# application = get_wsgi_application()

import os
import sys

# Add your project directory to the sys.path
path = '/home/aswinashi/Online-Kudumbasree-store'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'store.settings' # Adjust if your settings are elsewhere

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()