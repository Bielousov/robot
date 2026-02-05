import time
import sys
import select

from main import Pip

def start_app():
    robot = Pip()
    
    print("\n--- Robot Control Active ---")
    print("Commands: [Enter] = Prompt Fact | [s] + [Enter] = Sleep | [Ctrl+C] = Exit")

    try:
        # Start the robot's internal loops
        robot.run()

        robot.is_awake_state = 1

        while robot.running:
            # Non-blocking terminal check
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline().strip().lower()
                
                if line == "":
                    # Pure Enter key: High priority wake/fact request
                    print("[User] Action: PROMPTED")
                    robot.is_prompted = 1
                
                elif line == "s" or line == "esc":
                    # Force Sleep Transition
                    print("[User] Action: FORCE SLEEP")
                    # Set target to 0, but keep last at 1 so phase becomes -1
                    robot.is_awake_state = 0
                    # Ensure no lingering prompts wake him up immediately
                    robot.is_prompted = 0

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[System] Shutdown initiated...")
        
        # Trigger clean Neural Network goodbye if currently awake
        if robot.is_awake_state == 1:
            print("[System] Triggering Neural Network goodbye...")
            robot.is_awake_state = 0
            
            # Buffer to allow audio to finish playing
            time.sleep(1.0) 
        
        robot.running = False
        print("[System] Robot offline.")
        sys.exit(0)

if __name__ == "__main__":
    start_app()