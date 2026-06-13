import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
from sklearn.datasets import load_sample_image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_cnn_model(input_shape=(224, 224, 3), num_classes=4):
    """Create CNN model for medical image classification"""
    
    model = keras.Sequential([
        # Block 1
        layers.Conv2D(32, (3, 3), activation='relu', padding='same', input_shape=input_shape),
        layers.BatchNormalization(),
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Block 2
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Block 3
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Block 4
        layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Fully Connected Layers
        layers.Flatten(),
        layers.Dense(512, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    return model

def compile_model(model):
    """Compile the model"""
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    logger.info("✓ Model compiled successfully")
    return model

def create_and_save_model(model_path='models_data/medvision_model.h5'):
    """Create, train, and save the model"""
    
    logger.info("Creating CNN model...")
    model = create_cnn_model()
    
    logger.info("Compiling model...")
    model = compile_model(model)
    
    # Create dummy data for demonstration
    logger.info("Creating dummy training data...")
    X_train = np.random.rand(100, 224, 224, 3).astype('float32')
    y_train = keras.utils.to_categorical(np.random.randint(0, 4, 100), 4)
    
    X_val = np.random.rand(20, 224, 224, 3).astype('float32')
    y_val = keras.utils.to_categorical(np.random.randint(0, 4, 20), 4)
    
    logger.info("Training model on dummy data...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=5,
        batch_size=32,
        verbose=1
    )
    
    # Create directory if not exists
    import os
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    # Save model
    model.save(model_path)
    logger.info(f"✓ Model saved to {model_path}")
    
    return model

if __name__ == "__main__":
    create_and_save_model()
