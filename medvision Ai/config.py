import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'dcm'}
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    SECRET_KEY = os.getenv('SECRET_KEY', 'medvision_secret_key_2025')
    
    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'password')
    MYSQL_DB = os.getenv('MYSQL_DB', 'medvision_db')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    
    # Model Configuration
    MODEL_PATH = 'models_data/medvision_model.h5'
    TARGET_SIZE = (224, 224)
    
    # Disease Classes
    DISEASE_CLASSES = {
        0: "Normal",
        1: "Tumor Detected",
        2: "Fracture Detected",
        3: "Pneumonia Detected"
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
