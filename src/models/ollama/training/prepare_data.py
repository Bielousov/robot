#!/usr/bin/env python3
"""Prepare training/validation datasets from personality.jsonl."""
import json
import random
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <personality.jsonl> <output_dir>")
        sys.exit(1)

    source = Path(sys.argv[1])
    output = Path(sys.argv[2])

    rows = [
        json.loads(line)
        for line in source.read_text().splitlines()
        if line.strip()
    ]

    random.Random(7).shuffle(rows)
    validation_count = max(4, round(len(rows) * 0.15))

    output.mkdir(parents=True, exist_ok=True)

    (output / "valid.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows[:validation_count])
    )

    (output / "train.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows[validation_count:])
    )

    print(f"[train] train={len(rows) - validation_count}, valid={validation_count}")


if __name__ == "__main__":
    main()
