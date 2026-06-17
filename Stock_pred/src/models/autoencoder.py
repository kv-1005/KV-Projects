import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model

def build_autoencoder(input_dim: int, encoding_dim: int = 16):
    """
    Advanced deep autoencoder for dimension reduction and feature extraction.
    """
    input_layer = layers.Input(shape=(input_dim,))
    
    # Encoder
    x = layers.GaussianNoise(0.01)(input_layer)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.1)(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dense(32, activation='relu')(x)
    encoded_output = layers.Dense(encoding_dim, activation='relu')(x)
    
    # Decoder
    x = layers.Dense(32, activation='relu')(encoded_output)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dense(128, activation='relu')(x)
    decoded_output = layers.Dense(input_dim, activation='linear')(x)
    
    autoencoder = Model(input_layer, decoded_output)
    encoder = Model(input_layer, encoded_output)
    
    autoencoder.compile(optimizer='adam', loss='mse')
    return autoencoder, encoder


def train_autoencoder(X: np.ndarray, encoding_dim: int = 16, epochs: int = 50):
    """Train and return the encoder."""
    print(f"[Autoencoder] Training deep feature extractor (Encoding Dim: {encoding_dim})...")
    ae, encoder = build_autoencoder(X.shape[1], encoding_dim)
    ae.fit(X, X, epochs=epochs, batch_size=32, verbose=0)
    return encoder
