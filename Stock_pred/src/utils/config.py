from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    sequence_length: int = 60
    lstm_units_layer1: int = 100
    lstm_units_layer2: int = 50
    dropout_rate: float = 0.25
    learning_rate: float = 1e-3
    batch_size: int = 32
    max_epochs: int = 100
    early_stopping_patience: int = 10


@dataclass(frozen=True)
class FeatureConfig:
    use_technical_indicators: bool = True
    use_sentiment: bool = True
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_window: int = 20
    bb_std: float = 2.0
    sma_short: int = 5
    sma_medium: int = 20
    sma_long: int = 50
    sma_very_long: int = 200


@dataclass(frozen=True)
class TrainConfig:
    test_size_ratio: float = 0.2
    validation_size_ratio: float = 0.1
    random_seed: int = 42
    target_column: str = "Close"


