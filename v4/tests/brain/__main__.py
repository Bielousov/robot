import time
import sys
import threading
from main import AnimatronicRobot

def start_app():
    robot = AnimatronicRobot()
    
    # Simple listener for manual toggles
    def check_input():
        while robot.running:
            input() # Wait for Enter key
            
            # Toggle logic
            if robot.is_currently_awake == 1:
                print("\n[User] Signaling SLEEP...")
                robot.is_currently_awake = 0
            else:
                print("\n[User] Signaling AWAKE...")
                robot.is_currently_awake = 1

    # Run the keypress listener in a background thread
    input_thread = threading.Thread(target=check_input, daemon=True)
    input_thread.start()

    try:
        # Launch the robot's main loop
        robot.run()
    except KeyboardInterrupt:
        print("\n[System] Shutdown initiated...")
        
        # 1. Signal sleep state
        if robot.is_currently_awake == 1:
            print("[System] Finalizing Neural Network goodbye routine...")
            robot.is_currently_awake = 0
            
            # 2. WAIT for the NN to process the change and speak
            # We wait as long as the robot is "running". 
            # Your NN/Main loop should set robot.running = False AFTER goodbye is done.
            max_wait = 10 
            start_wait = time.time()
            while robot.running and (time.time() - start_wait < max_wait):
                time.sleep(0.1)
        
        # 3. Final hardware release
        robot.running = False
        print("[System] Robot offline.")
        sys.exit(0)

if __name__ == "__main__":
    start_app()