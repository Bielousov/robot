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
    ("pip what is your name", "YES"),
    ("pip what are you doing", "YES"),
    ("pip what time is it now", "YES"),
    ("pip what time is it", "YES"),
    ("pip tell me a job", "YES"),
    ("pip tell me a joke", "YES"),
    ("pip tell me about your hardware", "YES"),
    ("pip then tell me some fun fact", "YES"),
    ("pip what is the weather like today", "YES"),
    ("pip who are you", "YES"),
    ("hey pip", "YES"),

    # Same/similar prompts without explicit address
    ("what is your name", "NO"),
    ("what are you doing", "NO"),
    ("what time is it now", "NO"),
    ("what time is it", "NO"),
    ("tell me a job", "NO"),
    ("tell me a joke", "NO"),
    ("tell me about your hardware", "NO"),
    ("then tell me some fun fact", "NO"),
    ("what is the weather like today", "NO"),
    ("who are you", "NO"),

    # Clearly not addressed / conversational
    ("chips", "NO"),
    ("the dog is outside", "NO"),
    ("i think it will rain", "NO"),
    ("not sure what i do about this", "NO"),
    ("specialized hardware", "NO"),
    ("purple seven window banana", "NO"),
    ("immortal the table seventy five", "NO"),

    # Additional useful boundary cases
    ("can you help me", "NO"),
    ("can you read me a book", "NO"),
    ("read me a book", "NO"),
    ("i think we should leave soon", "NO"),
    ("hey what is your name", "NO"),
    ("hey what time is it", "NO"),
]


def run_test(llm, prompt):
    """Run one classification and return result + elapsed time."""

    start = time.perf_counter()

    score = llm.classify_conversation(prompt)

    elapsed = time.perf_counter() - start

    if score is None:
        actual = "ERROR"
    else:
        actual = "YES" if score >= 0.5 else "NO"

    return actual, score, elapsed


def benchmark():
    print("[Classifier Test] Initializing Mind...")

    # Mind initialization/model loading is not included in request timing.
    with Mind() as llm:
        print(f"[Classifier Test] Base Model: {llm.base_model}")
        print()

        print(
            f"{'Prompt':<42} | "
            f"{'Expected':<8} | "
            f"{'Actual':<6} | "
            f"{'Confidence':<12} | "
            f"{'Request Time':<12}"
        )

        print("-" * 100)

        passed = 0
        failed = 0

        for prompt, expected in PROMPTS:

            # Ensure every test is independent.
            llm.clear_history()

            actual, score, elapsed = run_test(llm, prompt)

            if score is None:
                score_text = "unavailable"
            else:
                score_text = f"{score:.8f}"

            print(
                f"{prompt:<42} | "
                f"{expected:<8} | "
                f"{actual:<6} | "
                f"{score_text:<12} | "
                f"{elapsed:.3f}s"
            )

            if actual == expected:
                passed += 1
            else:
                failed += 1

        # -------------------------------------------------------------
        # Summary
        # -------------------------------------------------------------

        print()
        print("=" * 100)
        print("CLASSIFIER TEST RESULTS")
        print("=" * 100)
        print(f"Total:  {len(PROMPTS)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        if PROMPTS:
            accuracy = passed / len(PROMPTS) * 100
            print(f"Accuracy: {accuracy:.1f}%")

        print("=" * 100)


if __name__ == "__main__":
    benchmark()