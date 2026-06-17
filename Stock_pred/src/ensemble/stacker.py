from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor


@dataclass
class StackingConfig:
    # Placeholder hyperparameters; tune as needed
    xgb_params: Dict = None

    def __post_init__(self):
        if self.xgb_params is None:
            self.xgb_params = {
                "n_estimators": 300,
                "max_depth": 4,
                "learning_rate": 0.05,
                "subsample": 0.9,
                "colsample_bytree": 0.9,
                "tree_method": "hist",
                "random_state": 42,
            }


class StackingMetaLearner:
    def __init__(self, cfg: StackingConfig | None = None):
        self.cfg = cfg or StackingConfig()
        self.model = XGBRegressor(**self.cfg.xgb_params)

    def fit(self, level0_preds: np.ndarray, y_true: np.ndarray) -> None:
        # level0_preds shape: (n_samples, n_models)
        self.model.fit(level0_preds, y_true)

    def predict(self, level0_preds: np.ndarray) -> np.ndarray:
        return self.model.predict(level0_preds)


