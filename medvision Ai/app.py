from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import os
import logging
from functools import wraps
from datetime import datetime
import json
from io import BytesIO
import numpy as np
from flask import send_file

# Import modules
from config import Config, config
from db_connect import db
from models import User, MedicalImage, DiagnosisReport, AIModel, Dashboard
from utils import allowed_file, save_uploaded_file, preprocess_image, get_disease_label, format_confidence
import tensorflow as tf
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Connect to database at startup
with app.app_context():
    if not db.connect():
        logger.error("Failed to connect to database. Check your MySQL credentials.")

# ==================== DECORATORS ====================

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = User.get_user(session['user_id'])
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        # Validation
        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        # Check if user exists
        existing = db.fetch_one(
            "SELECT * FROM users WHERE email = %s", (email,)
        )
        if existing:
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Register user
        if User.register(name, email, password):
            logger.info(f"New user registered: {email}")
            return jsonify({'success': True, 'message': 'Registration successful! Please login.'}), 201
        else:
            return jsonify({'success': False, 'message': 'Registration failed'}), 500
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        user = User.login(email, password)
        
        if user:
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            logger.info(f"User logged in: {email}")
            return jsonify({'success': True, 'message': 'Login successful', 'redirect': url_for('dashboard')}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    logger.info("User logged out")
    return redirect(url_for('login'))

# ==================== MAIN ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    user_id = session.get('user_id')
    user = User.get_user(user_id)
    
    # Get user statistics
    images = MedicalImage.get_user_images(user_id) or []
    reports = DiagnosisReport.get_user_reports(user_id) or []
    
    stats = {
        'total_images': len(images),
        'total_diagnoses': len(reports),
        'avg_confidence': round(np.mean([r['confidence'] for r in reports]), 2) if reports else 0
    }
    
    return render_template('dashboard.html', user=user, stats=stats)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload medical image"""
    if request.method == 'POST':
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['image']
        user_id = session.get('user_id')
        
        # Save file
        filepath = save_uploaded_file(file)
        if not filepath:
            return jsonify({'success': False, 'message': 'Invalid file type or size'}), 400
        
        # Get image type
        image_type = file.filename.rsplit('.', 1)[1].upper()
        
        # Store in database
        image_id = MedicalImage.upload_image(user_id, filepath, image_type)
        
        if image_id:
            logger.info(f"Image uploaded: {filepath}")
            return jsonify({
                'success': True,
                'message': 'Image uploaded successfully',
                'image_id': image_id,
                'redirect': url_for('analyze', image_id=image_id)
            }), 201
        else:
            return jsonify({'success': False, 'message': 'Failed to save image'}), 500
    
    return render_template('upload.html')

@app.route('/analyze/<int:image_id>', methods=['GET', 'POST'])
@login_required
def analyze(image_id):
    """Analyze medical image using AI"""
    image = MedicalImage.get_image(image_id)
    
    if not image:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Load and preprocess image
            preprocessed = preprocess_image(image['image_path'])
            
            if preprocessed is None:
                return jsonify({'success': False, 'message': 'Error processing image'}), 500
            
            # Load model
            model = tf.keras.models.load_model(Config.MODEL_PATH)
            
            # Make prediction
            predictions = model.predict(preprocessed, verbose=0)
            class_index = np.argmax(predictions[0])
            confidence = float(predictions[0][class_index]) * 100
            
            # Get disease label
            diagnosis = get_disease_label(class_index)
            
            # Save report
            report_id = DiagnosisReport.create_report(image_id, diagnosis, confidence)
            
            if report_id:
                logger.info(f"Diagnosis report created: {report_id}")
                return jsonify({
                    'success': True,
                    'diagnosis': diagnosis,
                    'confidence': format_confidence(confidence),
                    'report_id': report_id
                }), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to save report'}), 500
        
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('results.html', image=image)

@app.route('/results/<int:report_id>')
@login_required
def results(report_id):
    """View diagnosis results"""
    report = DiagnosisReport.get_report(report_id)
    
    if not report:
        return redirect(url_for('dashboard'))
    
    return render_template('results.html', report=report)

@app.route('/history')
@login_required
def history():
    """View patient diagnosis history"""
    user_id = session.get('user_id')
    reports = DiagnosisReport.get_user_reports(user_id) or []
    
    return render_template('history.html', reports=reports)

@app.route('/export-pdf/<int:report_id>')
@login_required
def export_pdf(report_id):
    report = DiagnosisReport.get_report(report_id)
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404

    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    # Content
    elements = []

    elements.append(Paragraph("MEDVISION AI - RADIOLOGY REPORT", styles['Title']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("PATIENT INFORMATION", styles['Heading2']))
    elements.append(Paragraph(f"Name: {report['name']}", styles['Normal']))
    elements.append(Paragraph(f"Email: {report['email']}", styles['Normal']))
    elements.append(Paragraph(f"Date: {report['created_date']}", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("EXAMINATION DETAILS", styles['Heading2']))
    elements.append(Paragraph("Modality: Chest X-ray", styles['Normal']))
    elements.append(Paragraph(f"Image Type: {report['image_type']}", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("AI FINDINGS", styles['Heading2']))
    elements.append(Paragraph(
        "The AI model detected abnormal patterns in lung regions that may indicate infection or inflammation.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("IMPRESSION", styles['Heading2']))
    elements.append(Paragraph(f"{report['diagnosis']}", styles['Normal']))
    elements.append(Paragraph(f"Confidence: {report['confidence']}%", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("RECOMMENDATIONS", styles['Heading2']))
    elements.append(Paragraph(
        "- Clinical correlation recommended<br/>"
        "- Follow-up imaging if required<br/>"
        "- Consult a radiologist",
        styles['Normal']
    ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("DISCLAIMER", styles['Heading2']))
    elements.append(Paragraph(
        "This AI-generated report is for assistive purposes only and not a substitute for professional medical advice.",
        styles['Italic']
    ))

    # Build PDF
    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='diagnosis_report.pdf',
        mimetype='application/pdf'
    )

# ==================== ADMIN ROUTES ====================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    stats = Dashboard.get_statistics()
    users = User.get_all_users()
    reports = DiagnosisReport.get_all_reports()
    models = AIModel.get_all_models()
    
    return render_template('admin.html', 
                         stats=stats, 
                         users=users, 
                         reports=reports, 
                         models=models)

@app.route('/api/statistics')
@admin_required
def get_statistics():
    """API endpoint for statistics"""
    stats = Dashboard.get_statistics()
    return jsonify(stats), 200

# ==================== API ROUTES ====================

@app.route('/api/user-profile')
@login_required
def get_user_profile():
    """Get user profile"""
    user = User.get_user(session.get('user_id'))
    return jsonify(user), 200

@app.route('/api/user-images')
@login_required
def get_user_images():
    """Get user's uploaded images"""
    images = MedicalImage.get_user_images(session.get('user_id')) or []
    return jsonify(images), 200

@app.route('/api/user-reports')
@login_required
def get_user_reports():
    """Get user's diagnosis reports"""
    reports = DiagnosisReport.get_user_reports(session.get('user_id')) or []
    return jsonify(reports), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {e}")
    return render_template('500.html'), 500

# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_user():
    """Inject user info into templates"""
    if 'user_id' in session:
        return {
            'current_user': User.get_user(session['user_id']),
            'is_admin': session.get('user_role') == 'admin'
        }
    return {}

# ==================== MAIN ====================

if __name__ == '__main__':
    # Create uploads directory
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs('models_data', exist_ok=True)
    
    # Check if model exists, if not create it
    if not os.path.exists(Config.MODEL_PATH):
        logger.info("Training model for the first time...")
        from train_model import create_and_save_model
        create_and_save_model(Config.MODEL_PATH)
    
    # Run app
    app.run(debug=True, host='0.0.0.0', port=5000)
