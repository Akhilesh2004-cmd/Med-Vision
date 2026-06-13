-- Create Database
CREATE DATABASE IF NOT EXISTS medvision_db;
USE medvision_db;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Medical Images Table
CREATE TABLE IF NOT EXISTS image (
    image_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    image_type VARCHAR(50) NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Diagnosis Reports Table
CREATE TABLE IF NOT EXISTS report (
    report_id INT PRIMARY KEY AUTO_INCREMENT,
    image_id INT NOT NULL,
    diagnosis VARCHAR(255) NOT NULL,
    confidence DECIMAL(5, 2) NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES image(image_id) ON DELETE CASCADE
);

-- AI Models Table
CREATE TABLE IF NOT EXISTS ai_model (
    model_id INT PRIMARY KEY AUTO_INCREMENT,
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    train_date DATE,
    accuracy DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patient History Table
CREATE TABLE IF NOT EXISTS patient_history (
    history_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    diagnosis_summary TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create Indexes for better performance
CREATE INDEX idx_user_id ON image(user_id);
CREATE INDEX idx_image_id ON report(image_id);
CREATE INDEX idx_user_reports ON report(image_id);

-- Insert sample admin user
INSERT INTO users (name, email, password, role) 
VALUES ('Admin', 'admin@medvision.com', 'scrypt:32768:8:1$QYw5VZB5hZAoXu1X$9d75f51cd8e0e9c6a91c0a6c5d4e3f2b1a0c9d8e7f6g5h4i3j2k1l0m9n8o7p6', 'admin');

-- Insert sample AI model
INSERT INTO ai_model (model_name, version, train_date, accuracy)
VALUES ('ResNet50', '1.0', CURDATE(), 95.50);
