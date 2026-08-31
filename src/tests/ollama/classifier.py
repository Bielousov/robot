import sys
import time
from pathlib import Path

# Path Logic
project_path = Path(__file__).parent.parent.parent.resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from lib.Mind import Mind


# ---------------------------------------------------------------------
# Test matrix
# ---------------------------------------------------------------------

PROMPTS = [
    # Explicitly addressed to Pip
    ("pip what is your name", "ADDRESSED"),
    ("pip what are you doing", "ADDRESSED"),
    ("pip what time is it now", "ADDRESSED"),
    ("pip what time is it", "ADDRESSED"),
    ("pip tell me a job", "ADDRESSED"),
    ("pip tell me a joke", "ADDRESSED"),
    ("pip tell me about your hardware", "ADDRESSED"),
    ("pip then tell me some fun fact", "ADDRESSED"),
    ("pip what is the weather like today", "ADDRESSED"),
    ("pip who are you", "ADDRESSED"),
    ("hey pip", "ADDRESSED"),

    # Same/similar prompts without explicit address
    ("what is your name", "AMBIGUOUS"),
    ("what are you doing", "AMBIGUOUS"),
    ("what time is it now", "AMBIGUOUS"),
    ("what time is it", "AMBIGUOUS"),
    ("tell me a job", "AMBIGUOUS"),
    ("tell me a joke", "AMBIGUOUS"),
    ("tell me about your hardware", "AMBIGUOUS"),
    ("then tell me some fun fact", "AMBIGUOUS"),
    ("what is the weather like today", "AMBIGUOUS"),
    ("who are you", "AMBIGUOUS"),

    # Clearly not addressed
    ("chips", "NOT_ADDRESSED"),
    ("the dog is outside", "NOT_ADDRESSED"),
    ("i think it will rain", "NOT_ADDRESSED"),
    ("not sure what i do about this", "NOT_ADDRESSED"),
    ("specialized hardware", "NOT_ADDRESSED"),
    ("purple seven window banana", "NOT_ADDRESSED"),
    ("immortal the table seventy five", "NOT_ADDRESSED"),

    # Additional boundary cases
    ("can you read me a book", "AMBIGUOUS"),
    ("can you help me", "AMBIGUOUS"),
    ("read me a book", "AMBIGUOUS"),
    ("i think we should leave soon", "NOT_ADDRESSED"),
    ("hey what is your name", "ADDRESSED"),
    ("hey what time is it", "ADDRESSED"),
]


def run_test(llm, prompt):
    """Run one classification and return label, score, and elapsed time."""

    start = time.perf_counter()

    score = llm.classify_conversation(prompt)

    elapsed = time.perf_counter() - start

    # classify_conversation() should expose the actual classification.
    actual = getattr(llm, "last_classification", None)

    if actual is None:
        actual = "?"

    return actual, score, elapsed


def benchmark():
    print("[Classifier Test] Initializing Mind...")

    # Model initialization/loading is not included in request timing.
    with Mind() as llm:
        print(f"[Classifier Test] Base Model: {llm.base_model}")
        print()

        print(
            f"{'Prompt':<42} | "
            f"{'Expected':<15} | "
            f"{'Actual':<15} | "
            f"{'Confidence':<12} | "
            f"{'Request Time':<12}"
        )

        print("-" * 115)

        passed = 0
        failed = 0

        for prompt, expected in PROMPTS:

            # Keep every classification independent.
            llm.clear_history()

            actual, score, elapsed = run_test(llm, prompt)

            score_text = (
                f"{score:.8f}"
                if score is not None
                else "unavailable"
            )

            print(
                f"{prompt:<42} | "
                f"{expected:<15} | "
                f"{actual:<15} | "
                f"{score_text:<12} | "
                f"{elapsed:.3f}s"
            )

            # ---------------------------------------------------------
            # Evaluate result
            # ---------------------------------------------------------

            if actual == expected:
                passed += 1
            else:
                failed += 1

        # -------------------------------------------------------------
        # Results
        # -------------------------------------------------------------

        print()
        print("=" * 115)
        print("CLASSIFIER TEST RESULTS")
        print("=" * 115)

        print(f"Total:    {len(PROMPTS)}")
        print(f"Passed:   {passed}")
        print(f"Failed:   {failed}")

        if PROMPTS:
            accuracy = passed / len(PROMPTS) * 100
            print(f"Accuracy: {accuracy:.1f}%")

        print("=" * 115)


if __name__ == "__main__":
    benchmark()