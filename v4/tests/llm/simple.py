import os
import time
from ollama import Client

# Path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../"))
MODELS_DIR = os.path.join(PROJECT_ROOT, "lib/ollama/models")

def run_test():
    os.environ["OLLAMA_MODELS"] = MODELS_DIR
    client = Client(host='http://localhost:11434')

    print(f"[Test] Prompting Pip...")
    
    # --- Start Timer ---
    start_time = time.perf_counter()

    try:
        response = client.chat(
            model='pip',
            messages=[{'role': 'user', 'content': 'Say something sarcastic about a slow computer.'}],
            options={
                'temperature': 1.0,
                'num_thread': 4  # Specifically pin to the 4 high-perf cores of the RPi5
            },
            keep_alive=-1  # Use a massive string instead of 0 or -1
        )
        
        # --- End Timer ---
        end_time = time.perf_counter()
        execution_time = end_time - start_time

        print("\n--- Pip's Response ---")
        print(response.message.content)
        print("----------------------")
        print(f"⏱️  Execution Time: {execution_time:.2f} seconds")
        
        if execution_time > 5:
            print("💡 Note: That was slow. It was likely loading from the SD card.")
        else:
            print("🚀 Note: Snappy response! The model is running from RAM.")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    run_test()