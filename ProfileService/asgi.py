"""
ASGI config for ProfileService project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

try:
    from django.core.asgi import get_asgi_application
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProfileService.settings')
    
    logger.info(f"Loading Django settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    logger.info(f"DATABASE_URL set: {bool(os.environ.get('DATABASE_URL'))}")
    logger.info(f"SECRET_KEY set: {bool(os.environ.get('SECRET_KEY'))}")
    
    application = get_asgi_application()
    
    logger.info("✓ ASGI application initialized successfully")
    
except Exception as e:
    logger.error(f"✗ Failed to initialize ASGI application: {e}", exc_info=True)
    raise