"""
logging_config.py — Compatibility stub.
Provides setup_logging() and get_logger() for modules that import it.
"""
import logging

def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

def get_logger(name: str = __name__) -> logging.Logger:
    return logging.getLogger(name)
