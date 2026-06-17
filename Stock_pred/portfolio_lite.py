"""
Stock Prediction AI - Portfolio/Resume Version
----------------------------------------------
A condensed version of the end-to-end CNN-LSTM stock prediction pipeline.
Features: Technical indicators, simplified VADER sentiment, CNN-LSTM hybrid model, and backtesting metrics.

Author: [Your Name]

Usage:
    python portfolio_lite.py
"""

import numpy as np
import pandas as pd
import yfinance as yf
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.preprocessing import MinMaxScaler
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# ----------------------------------------------------
# 1. Data Pipeline
# ----------------------------------------------------
def fetch_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch structured historical OHLCV data from Yahoo Finance."""
    print(f"Fetching data for {ticker} from {start} to {end}...")
    df = yf.download(ticker, start=start, end=end, progress=False)
    # Ensure MultiIndex columns are flattened if using yfinance >= 0.2.0
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    return df

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer technical features (SMA, RSI, returns) to aid the neural network."""
    # Simple Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # Relative Strength Index (RSI)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
    
    df = df.dropna()
    return df

def add_sentiment_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Simulate merging VADER NLP sentiment for demonstration purposes."""
    try:
        nltk.download('vader_lexicon', quiet=True)
        # In a production pipeline, this joins live news feeds (e.g. Finnhub).
        # We simulate the -1 to 1 sentiment metric here.
        df['Sentiment'] = np.random.uniform(-0.1, 0.5, len(df))
    except Exception:
        df['Sentiment'] = 0.0
    return df

# ----------------------------------------------------
# 2. Sequential Data Preparation
# ----------------------------------------------------
def prepare_sequences(df: pd.DataFrame, target_col='Close', seq_len=60):
    """Normalize and construct 3D tensors for LSTM sequence ingesting."""
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df.values)
    
    target_idx = df.columns.get_loc(target_col)
    X, y = [], []
    
    for i in range(seq_len, len(scaled_data)):
        X.append(scaled_data[i-seq_len : i])
        y.append(scaled_data[i, target_idx])
        
    return np.array(X), np.array(y), scaler

# ----------------------------------------------------
# 3. Model Architecture
# ----------------------------------------------------
def build_cnn_lstm(input_shape):
    """Architect hybrid CNN-LSTM with optimized learning rate & dropout."""
    inputs = layers.Input(shape=input_shape)
    
    # Feature Extraction (CNN)
    x = layers.Conv1D(filters=64, kernel_size=3, padding="same", activation="relu")(inputs)
    x = layers.MaxPool1D(pool_size=2)(x)
    x = layers.Conv1D(filters=64, kernel_size=3, padding="same", activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    
    # Sequence Modeling (LSTM)
    x = layers.LSTM(100, return_sequences=True)(x)
    x = layers.Dropout(0.25)(x)
    x = layers.LSTM(50)(x)
    x = layers.Dropout(0.25)(x)
    
    # Fully connected block
    x = layers.Dense(64, activation="relu")(x)
    outputs = layers.Dense(1, activation="linear")(x)
    
    model = models.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer=optimizers.Adam(learning_rate=1e-3), loss="mse")
    return model

# ----------------------------------------------------
# 4. Main Pipeline Execution
# ----------------------------------------------------
def main():
    print("Initializing Stock Prediction AI Engine...")
    ticker = "AAPL"
    
    # Run Preprocessing Pipeline
    df = fetch_data(ticker, "2020-01-01", "2024-01-01")
    df = add_technical_indicators(df)
    df = add_sentiment_scores(df)
    
    print(f"Data ingested. Final shape: {df.shape}. Columns: {list(df.columns)}")
    
    # Generate Train/Test Splits
    X, y, scaler = prepare_sequences(df, seq_len=60)
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    # Model Construction
    print("Building hybrid deep architecture...")
    model = build_cnn_lstm(input_shape=(X_train.shape[1], X_train.shape[2]))
    # model.summary() # Uncomment to see params overview
    
    # Subsample training for showcase speed
    print("Starting lightweight training epoch...")
    model.fit(
        X_train, y_train, 
        epochs=1, 
        batch_size=32, 
        validation_split=0.1, 
        verbose=1
    )
    
    # Evaluation Validation
    print("Backtesting Evaluation...")
    loss = model.evaluate(X_test, y_test, verbose=0)
    
    # Directional Accuracy approximation (for demo)
    y_pred = model.predict(X_test, verbose=0).flatten()
    dir_acc = np.mean(np.sign(y_pred[1:] - y_test[:-1]) == np.sign(y_test[1:] - y_test[:-1]))
    
    print("-" * 50)
    print("Portfolio Snapshot Completed!")
    print(f"Ticker: {ticker}")
    print(f"Test Set MSE Score:       {loss:.4f}")
    print(f"Directional Accuracy:     {dir_acc * 100:.2f}%")
    print("-" * 50)

if __name__ == "__main__":
    main()
