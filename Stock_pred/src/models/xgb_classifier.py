from __future__ import annotations

from typing import Optional

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier


def compute_scale_pos_weight(y: np.ndarray) -> float:
    # Avoid division by zero; computes (neg/pos)
    pos = float((y == 1).sum())
    neg = float((y == 0).sum())
    if pos == 0:
        return 1.0
    return max(1.0, neg / pos)


def build_xgb_classifier(base_params: Optional[dict] = None, scale_pos_weight: Optional[float] = None) -> XGBClassifier:
    params = {
        "n_estimators": 500,
        "learning_rate": 0.05,
        "max_depth": 6,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 10,
        "reg_lambda": 1.0,
        "tree_method": "hist",
        "random_state": 42,
        "n_jobs": 0,
        **(base_params or {}),
    }
    if scale_pos_weight is not None:
        params["scale_pos_weight"] = scale_pos_weight
    return XGBClassifier(**params)


def fit_calibrated(model: XGBClassifier, X_tr: np.ndarray, y_tr: np.ndarray, cv: int = 3) -> CalibratedClassifierCV:
    # Platt scaling via sigmoid with internal cross-validation (robust to class presence in folds)
    calibrated = CalibratedClassifierCV(model, method="sigmoid", cv=cv)
    calibrated.fit(X_tr, y_tr)
    return calibrated


