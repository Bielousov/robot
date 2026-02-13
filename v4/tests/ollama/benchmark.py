import sys
import time
import statistics
from pathlib import Path

# Path Logic
v4_path = Path(__file__).parent.parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from lib.LLMService import LLMService

# -------- config --------
ITERATIONS = 10
WARMUP_RUNS = 1
PROMPT = "Briefly explain why the sky appears blue to a human observer, using exactly one sentence without using the word 'scattering'."

def run_once(llm):
    """Executes a single inference and returns the duration."""
    start = time.perf_counter()
    llm.think(PROMPT)
    return time.perf_counter() - start

def benchmark():
    print("[Benchmark] Initializing LLMService...")
    
    # Initialize service - model creation/loading is NOT timed here
    with LLMService() as llm:
        print(f"[Benchmark] Base Model: {llm.base_model}")
        
        print(f"[Benchmark] Warming up model ({WARMUP_RUNS} runs)...")
        for _ in range(WARMUP_RUNS):
            run_once(llm)
            llm.clear_history() # Keep the benchmark consistent

        print(f"[Benchmark] Running {ITERATIONS} timed iterations...")
        times = []
        for i in range(ITERATIONS):
            # We clear history before each run to ensure the prompt 
            # size remains identical for every iteration
            llm.clear_history()
            
            t = run_once(llm)
            times.append(t)
            print(f"  Run {i+1:02d}: {t:.2f}s")

        print("\n" + "="*21)
        print("   BENCHMARK RESULTS   ")
        print("="*21)
        print(f"Total Iterations: {ITERATIONS}")
        print(f"Fastest Run:      {min(times):.2f}s")
        print(f"Average Time:     {statistics.mean(times):.2f}s")
        print(f"Median Time:      {statistics.median(times):.2f}s")
        
        if ITERATIONS >= 4:
            # P95 calculation
            p95 = statistics.quantiles(times, n=20)[18]
            print(f"P95 Latency:      {p95:.2f}s")
            
        print(f"Slowest Run:      {max(times):.2f}s")
        print("="*21)

if __name__ == "__main__":
    benchmark()