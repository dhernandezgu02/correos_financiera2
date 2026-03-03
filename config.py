import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-cambiar-en-produccion')

# Database
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Upload
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Email SMTP (Outlook/Office365)
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.office365.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', 'jrocha@cnccol.com')  # Configurar con tu email
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'Consultoria2025*')  # Configurar con tu contraseña
SMTP_FROM = os.environ.get('SMTP_FROM', 'jrocha@cnccol.com')  # Email remitente

# Scheduler
EMAIL_INTERVAL_DAYS = 3

# Semaforización (días)
SEMAFORO_AMARILLO_DIAS = 30  # Amarillo: vence en los próximos 30 días
