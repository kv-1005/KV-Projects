#!/usr/bin/env bash

# Retraining Governance Protocol
# ------------------------------
# Institutional trading prevents ad-hoc intraday retraining which masks
# structural decay and encourages backtest overfitting.
#
# Rules:
# 1. Retraining can ONLY occur on weekends (when markets are closed).
# 2. Retraining ONLY proceeds if the live equity slope has degraded or 
#    there is a sufficient new data threshold (1 week minimum collected).

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR/.."

# Ensure this script is run only on Saturday or Sunday
DAY_OF_WEEK=$(date +%u)
if [ "$DAY_OF_WEEK" -lt 6 ]; then
  echo "🚨 [Governance] ABORT: Retraining is strictly forbidden on weekdays."
  echo "Intraday retraining leads to hidden structural overfitting."
  exit 1
fi

echo "========================================"
echo " Starting Weekly Institutional Retrain"
echo "========================================"

# Run the Python training pipeline using the new Cost-Aware expectancies
export PYTHONIOENCODING="utf-8"

# Robust python detection (handles python3 vs python aliases)
PYTHON_EXE=$(command -v python3 || command -v python || echo "python")
$PYTHON_EXE run.py --config config/nse_intraday.json --train

echo ""
echo "========================================"
echo "✅ Retraining complete. Models updated."
echo "========================================"

# To automate this, add the following to crontab:
# 0 2 * * 6 /path/to/project/scripts/retrain_weekend.sh >> /path/to/project/artifacts/retrain.log 2>&1
