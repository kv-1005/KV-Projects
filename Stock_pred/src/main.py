import argparse
from datetime import datetime

from rich.console import Console

from src.training.train import run_training_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stock Prediction AI - CNN-LSTM pipeline")
    parser.add_argument("--ticker", type=str, required=True, help="Ticker symbol (e.g., AAPL)")
    parser.add_argument("--start", type=str, required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--window", type=int, default=60, help="Sequence length / lookback window")
    parser.add_argument("--epochs", type=int, default=100, help="Max epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=1e-3, help="Learning rate for Adam")
    parser.add_argument("--save_dir", type=str, default="artifacts", help="Directory to save models/plots")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    console = Console()

    console.log(f"Starting training for {args.ticker} from {args.start} to {args.end}")

    start_date = datetime.fromisoformat(args.start)
    end_date = datetime.fromisoformat(args.end)

    results = run_training_pipeline(
        ticker=args.ticker,
        start_date=start_date,
        end_date=end_date,
        sequence_length=args.window,
        max_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        save_dir=args.save_dir,
    )

    console.rule("Results")
    for key, value in results.items():
        console.print(f"[bold]{key}[/]: {value}")


if __name__ == "__main__":
    main()


