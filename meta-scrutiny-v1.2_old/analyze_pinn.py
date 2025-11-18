#!/usr/bin/env python3
import sys
import json
import gzip
import argparse
from pathlib import Path
import pandas as pd

def load_log_file(log_path: Path):
    if not log_path.exists():
        print(f"[ERROR] Log file not found: {log_path}")
        sys.exit(1)
    with gzip.open(log_path, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log_file", type=str, help="Path to .json.gz log")
    parser.add_argument("-n", "--top-n", type=int, default=5)
    args = parser.parse_args()
    data = load_log_file(Path(args.log_file))
    if "all_trials" not in data or not data["all_trials"]:
        print("[WARN] 'all_trials' is empty.")
        print("Best:", data.get("best_value"), data.get("best_params"))
        return
    records = []
    for t in data["all_trials"]:
        rec = {"loss": t["value"], **t.get("params", {})}
        records.append(rec)
    df = pd.DataFrame(records).sort_values("loss")
    print(df.head(args.top_n).to_string(index=False))
    print("Best params:", data["best_params"])

if __name__ == "__main__":
    main()