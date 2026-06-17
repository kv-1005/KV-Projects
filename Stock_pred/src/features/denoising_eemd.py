import numpy as np
import pandas as pd
from PyEMD import EMD, EEMD
from sklearn.preprocessing import StandardScaler

def eemd_denoise_series(data: pd.Series, trials: int = 10, noise_width: float = 0.05) -> pd.Series:
    """
    Empirical Mode Decomposition (EEMD) based signal denoising.
    Decomposes signal into IMFs and reconstructs using meaningful components.
    """
    if data.isnull().any():
        data = data.fillna(method='ffill').fillna(method='bfill')
        
    vals = data.values
    eemd = EEMD()
    eemd.trials = trials
    eemd.noise_width = noise_width
    
    # Perform decomposition
    IMFs = eemd.eemd(vals)
    
    # Reconstruct: Typically exclude the highest frequency IMF (first 1-2 components)
    # which usually contain noise. 
    # Use IMFs[1:] or IMFs[2:] based on signal quality.
    if IMFs.shape[0] > 2:
        reconstructed = np.sum(IMFs[2:], axis=0) # Removing first two high-freq components
    else:
        reconstructed = np.sum(IMFs, axis=0)
        
    return pd.Series(reconstructed, index=data.index)

def add_eemd_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds EEMD-denoised Close and volatility features.
    """
    df = df.copy()
    if "Close" in df.columns:
        print("[Feature] Applying EEMD Signal Denoising (High Precision)...")
        df["Close_eemd"] = eemd_denoise_series(df["Close"])
    return df
