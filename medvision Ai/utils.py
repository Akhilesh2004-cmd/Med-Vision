import cv2
import numpy as np
import os
from werkzeug.utils import secure_filename
from config import Config
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def preprocess_image(image_path, target_size=Config.TARGET_SIZE):
    """Preprocess medical image for CNN model"""
    try:
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not read image: {image_path}")
            return None
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize to target size
        image = cv2.resize(image, target_size)
        
        # Normalize pixel values to 0-1
        image = image.astype('float32') / 255.0
        
        # Add batch dimension
        image = np.expand_dims(image, axis=0)
        
        logger.info(f"✓ Image preprocessed successfully: {image_path}")
        return image
    
    except Exception as e:
        logger.error(f"✗ Error preprocessing image: {e}")
        return None

def save_uploaded_file(file):
    """Save uploaded file to disk"""
    try:
        if not file or file.filename == '':
            logger.error("No file provided")
            return None
        
        if not allowed_file(file.filename):
            logger.error(f"File type not allowed: {file.filename}")
            return None
        
        # Create uploads folder if not exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        timestamp = str(int(__import__('time').time()))
        filename = f"{timestamp}_{filename}"
        
        # Save file
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        logger.info(f"✓ File saved successfully: {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"✗ Error saving file: {e}")
        return None

def get_disease_label(class_index):
    """Convert class index to disease label"""
    return Config.DISEASE_CLASSES.get(class_index, "Unknown")

def format_confidence(confidence):
    """Format confidence score"""
    return round(float(confidence), 2)

def generate_report_data(diagnosis, confidence, image_path):
    """Generate report data dictionary"""
    return {
        'diagnosis': diagnosis,
        'confidence': format_confidence(confidence),
        'timestamp': __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'image_path': image_path
    }


def delete_file(filepath):
    """Delete file from disk"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"✓ File deleted: {filepath}")
            return True
        return False
    except Exception as e:
        logger.error(f"✗ Error deleting file: {e}")
        return False
