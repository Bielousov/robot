import time
import sys
from main import AnimatronicRobot

def start_app():
    robot = AnimatronicRobot()
    
    try:
        # Launch the robot's main loop
        robot.run()
    except KeyboardInterrupt:
        print("\n[System] Shutdown requested via Ctrl+C...")
        
        # 1. Force the goodbye state
        # We manually trigger the goodbye logic
        if robot.is_currently_awake:
            robot.speak("goodbye")
            robot.is_currently_awake = 0
            
        # 2. Small delay to allow print/speech to finish
        print("[System] Waiting for graceful exit...")
        time.sleep(1) 
        
        # 3. Stop threads and exit
        robot.running = False
        print("[System] Robot offline.")
        sys.exit(0)

if __name__ == "__main__":
    start_app()