from db_connect import db
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class User:
    """User Model"""
    
    @staticmethod
    def register(name, email, password, role='user'):
        """Register a new user"""
        hashed_password = generate_password_hash(password)
        query = """
            INSERT INTO users (name, email, password, role) 
            VALUES (%s, %s, %s, %s)
        """
        success = db.execute_query(query, (name, email, hashed_password, role))
        return success
    
    @staticmethod
    def login(email, password):
        """Authenticate user"""
        query = "SELECT * FROM users WHERE email = %s"
        user = db.fetch_one(query, (email,))
        
        if user and check_password_hash(user['password'], password):
            return user
        return None
    
    @staticmethod
    def get_user(user_id):
        """Get user by ID"""
        query = "SELECT * FROM users WHERE user_id = %s"
        return db.fetch_one(query, (user_id,))
    
    @staticmethod
    def get_all_users():
        """Get all users"""
        query = "SELECT user_id, name, email, role FROM users"
        return db.fetch_all(query)
    
    @staticmethod
    def update_profile(user_id, name, email):
        """Update user profile"""
        query = "UPDATE users SET name = %s, email = %s WHERE user_id = %s"
        return db.execute_query(query, (name, email, user_id))

class MedicalImage:
    """Medical Image Model"""
    
    @staticmethod
    def upload_image(user_id, image_path, image_type):
        """Store image upload record"""
        query = """
            INSERT INTO image (user_id, image_path, image_type, upload_date) 
            VALUES (%s, %s, %s, NOW())
        """
        success = db.execute_query(query, (user_id, image_path, image_type))
        if success:
            query_fetch = "SELECT LAST_INSERT_ID() as image_id"
            result = db.fetch_one(query_fetch)
            return result['image_id'] if result else None
        return None
    
    @staticmethod
    def get_user_images(user_id):
        """Get all images of a user"""
        query = """
            SELECT image_id, image_path, image_type, upload_date 
            FROM image WHERE user_id = %s 
            ORDER BY upload_date DESC
        """
        return db.fetch_all(query, (user_id,))
    
    @staticmethod
    def get_image(image_id):
        """Get specific image"""
        query = "SELECT * FROM image WHERE image_id = %s"
        return db.fetch_one(query, (image_id,))
    
    @staticmethod
    def delete_image(image_id):
        """Delete image record"""
        query = "DELETE FROM image WHERE image_id = %s"
        return db.execute_query(query, (image_id,))

class DiagnosisReport:
    """Diagnosis Report Model"""
    
    @staticmethod
    def create_report(image_id, diagnosis, confidence):
        """Create diagnosis report"""
        query = """
            INSERT INTO report (image_id, diagnosis, confidence, created_date) 
            VALUES (%s, %s, %s, NOW())
        """
        success = db.execute_query(query, (image_id, diagnosis, confidence))
        if success:
            query_fetch = "SELECT LAST_INSERT_ID() as report_id"
            result = db.fetch_one(query_fetch)
            return result['report_id'] if result else None
        return None
    
    @staticmethod
    def get_report(report_id):
        """Get specific report"""
        query = """
            SELECT r.*, i.image_path, i.image_type, u.name, u.email 
            FROM report r 
            JOIN image i ON r.image_id = i.image_id 
            JOIN users u ON i.user_id = u.user_id 
            WHERE r.report_id = %s
        """
        return db.fetch_one(query, (report_id,))
    
    @staticmethod
    def get_user_reports(user_id):
        """Get all reports for a user"""
        query = """
            SELECT r.report_id, r.image_id, r.diagnosis, r.confidence, r.created_date, i.image_type 
            FROM report r 
            JOIN image i ON r.image_id = i.image_id 
            WHERE i.user_id = %s 
            ORDER BY r.created_date DESC
        """
        return db.fetch_all(query, (user_id,))
    
    @staticmethod
    def get_all_reports():
        """Get all reports (Admin)"""
        query = """
            SELECT r.report_id, r.diagnosis, r.confidence, r.created_date, 
                   u.name, u.email, i.image_type 
            FROM report r 
            JOIN image i ON r.image_id = i.image_id 
            JOIN users u ON i.user_id = u.user_id 
            ORDER BY r.created_date DESC
        """
        return db.fetch_all(query)

class AIModel:
    """AI Model Information"""
    
    @staticmethod
    def add_model(model_name, version, accuracy):
        """Add AI model record"""
        query = """
            INSERT INTO ai_model (model_name, version, train_date, accuracy) 
            VALUES (%s, %s, NOW(), %s)
        """
        return db.execute_query(query, (model_name, version, accuracy))
    
    @staticmethod
    def get_latest_model():
        """Get latest model info"""
        query = """
            SELECT * FROM ai_model 
            ORDER BY train_date DESC LIMIT 1
        """
        return db.fetch_one(query)
    
    @staticmethod
    def get_all_models():
        """Get all models"""
        query = "SELECT * FROM ai_model ORDER BY train_date DESC"
        return db.fetch_all(query)

class Dashboard:
    """Dashboard Statistics"""
    
    @staticmethod
    def get_statistics():
        """Get system statistics for admin dashboard"""
        stats = {}
        
        # Total users
        query = "SELECT COUNT(*) as count FROM users"
        result = db.fetch_one(query)
        stats['total_users'] = result['count'] if result else 0
        
        # Total diagnoses
        query = "SELECT COUNT(*) as count FROM report"
        result = db.fetch_one(query)
        stats['total_diagnoses'] = result['count'] if result else 0
        
        # Total images
        query = "SELECT COUNT(*) as count FROM image"
        result = db.fetch_one(query)
        stats['total_images'] = result['count'] if result else 0
        
        # Average confidence
        query = "SELECT AVG(confidence) as avg_conf FROM report"
        result = db.fetch_one(query)
        stats['avg_confidence'] = round(result['avg_conf'], 2) if result and result['avg_conf'] else 0
        
        return stats
