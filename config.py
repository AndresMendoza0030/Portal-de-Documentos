import os
from dotenv import load_dotenv

load_dotenv()  # Cargar variables de entorno desde un archivo .env si existe

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
    BACKUP_FOLDER = os.path.join(os.getcwd(), 'backups')
    TEMP_FOLDER = os.getenv('TEMP_FOLDER', 'temp/')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
