from __future__ import annotations

from typing import Tuple

import tensorflow as tf
from tensorflow.keras import callbacks, layers, models, optimizers


def build_cnn_lstm_model(
    input_shape: Tuple[int, int],
    lstm_units_1: int = 100,
    lstm_units_2: int = 50,
    dropout_rate: float = 0.25,
    learning_rate: float = 1e-3,
) -> tf.keras.Model:
    inputs = layers.Input(shape=input_shape)

    x = layers.Conv1D(filters=64, kernel_size=3, padding="same", activation="relu")(inputs)
    x = layers.MaxPool1D(pool_size=2)(x)
    x = layers.Conv1D(filters=64, kernel_size=3, padding="same", activation="relu")(x)
    x = layers.Dropout(dropout_rate)(x)

    x = layers.LSTM(lstm_units_1, return_sequences=True)(x)
    x = layers.Dropout(dropout_rate)(x)
    x = layers.LSTM(lstm_units_2)(x)
    x = layers.Dropout(dropout_rate)(x)

    x = layers.Dense(64, activation="relu")(x)
    outputs = layers.Dense(1, activation="linear")(x)

    model = models.Model(inputs=inputs, outputs=outputs)
    optimizer = optimizers.Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss="mse")
    return model


def default_callbacks(save_path: str, patience: int = 10) -> list[callbacks.Callback]:
    return [
        callbacks.EarlyStopping(monitor="val_loss", patience=patience, restore_best_weights=True, verbose=1),
        callbacks.ModelCheckpoint(filepath=save_path, monitor="val_loss", save_best_only=True, verbose=1),
        callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=max(2, patience // 3), verbose=1),
    ]


