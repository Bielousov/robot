import json
import random
from pathlib import Path

source = Path("src/models/llm/personalized/personality.jsonl")
output = source.parent / "data"
rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
random.Random(7).shuffle(rows)

validation_count = max(4, round(len(rows) * 0.15))
(output / "valid.jsonl").write_text(
    "".join(json.dumps(row) + "\n" for row in rows[:validation_count])
)
(output / "train.jsonl").write_text(
    "".join(json.dumps(row) + "\n" for row in rows[validation_count:])
)
print(f"train={len(rows) - validation_count}, valid={validation_count}")