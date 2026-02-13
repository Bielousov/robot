import sys, time
from pathlib import Path

# Path Logic
v4_path = Path(__file__).parent.parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from v4.lib.Mind import Mind 

def run_test():
    print("[Test] Initializing Robot Brain Service...")
    
    # Init happens HERE (Server start + Model Create) - excluded from timer
    with Mind() as llm:
        
        # --- WARM-UP (Optional but recommended for Pi 5) ---
        # This ensures the model is fully resident in RAM before we time it
        print("[Test] Warming up engine...")
        llm.think("System check.") 
        llm.clear_history() # Clear warm-up from history to keep test clean

        test_prompt = "Hi, I'm Anton, your master and creator. Say how you feel about being created."
        
        print(f"[Test] Prompting Pip: '{test_prompt}'")
        
        # --- Start Timer: Pure Inference Only ---
        start_time = time.perf_counter()

        try:
            response = llm.think(test_prompt)
            
            # --- End Timer ---
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            print("\n--- Response ---")
            print(f"Pip: {response}")
            print("----------------------")
            print(f"⏱️  Inference Latency: {execution_time:.2f} seconds")
            
            # Verify history
            print(f"🧠 Context Window: {len(llm.history)} messages")
            
            if execution_time < 3:
                print("🚀 Note: Exceptional speed for a Pi 5!")
            elif execution_time < 7:
                print("⚡ Note: Standard performance.")
            else:
                print("🐢 Note: High latency detected. Check CPU thermal throttling.")

        except Exception as e:
            print(f"Test failed: {e}")

if __name__ == "__main__":
    run_test()