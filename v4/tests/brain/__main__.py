import time
import sys
import threading
from main import AnimatronicRobot

def start_app():
    robot = AnimatronicRobot()
    
    # Simple listener for manual toggles (optional helper)
    def check_input():
        while robot.running:
            # Example: hit Enter to toggle state
            input() 
            new_state = 0 if robot.is_currently_awake else 1
            print(f"\n[User] Toggling state to: {'AWAKE' if new_state else 'SLEEP'}")
            robot.is_currently_awake = new_state

    # Run the keypress listener in a background thread
    input_thread = threading.Thread(target=check_input, daemon=True)
    input_thread.start()

    try:
        # Launch the robot's main loop
        robot.run()
    except KeyboardInterrupt:
        print("\n[System] Shutdown requested. Signaling Neural Network...")
        
        # 1. Signal the state change
        robot.is_currently_awake = 0
            
        # 2. Wait for the Neural Network to transition and speak
        # We loop while the robot is still "running" (the NN will set this to False when done)
        # or we wait for a specific flag that the goodbye is finished.
        print("[System] Waiting for robot to finalize sleep routine...")
        
        timeout = 5  # Max seconds to wait for goodbye speech
        start_wait = time.time()
        
        while robot.running and (time.time() - start_wait < timeout):
            # If your robot.run() logic sets robot.running=False 
            # after the goodbye, this loop will exit perfectly.
            time.sleep(0.1)
        
        # 3. Final cleanup
        robot.running = False
        print("[System] Robot offline.")
        sys.exit(0)

if __name__ == "__main__":
    start_app()