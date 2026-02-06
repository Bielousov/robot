import time
import sys
import select
from main import Pip

def start_app():
    robot = Pip()
    
    print("\n--- Robot Control Active ---")
    print("Commands: [Enter] = Prompt Fact | [s] = Sleep | [Ctrl+C] = Exit")

    try:
        # Start the robot's internal loops (Brain and Logic)
        robot.run()

        # Initial start state
        robot.state.is_awake_state = True

        while True:
            # Non-blocking terminal check for user input
            # select.select monitors stdin for 0.1s
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline().strip().lower()
                
                if line == "":
                    # Pure Enter key: Set prompt flag for the next Brain tick
                    print("[User] Action: PROMPTED")
                    robot.state.is_prompted = True
                
                elif line in ["s", "esc"]:
                    # Force Sleep Transition
                    print("[User] Action: FORCE SLEEP")
                    # Transition logic handled by IntentHandler in next tick
                    robot.state.is_awake_state = False
                    robot.state.is_prompted = False

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[System] Shutdown initiated...")
        
        # Trigger clean Neural Network goodbye if currently awake
        if robot.state.is_awake_state:
            print("[System] Triggering Neural Network goodbye...")
            robot.state.is_awake_state = False
            # Wait a moment for the logic thread to pick up the state change 
            # and for the voice to actually say "goodbye"
            time.sleep(1.5) 
        
        # Cleanly stop the custom threads
        robot.stop()
        print("[System] Robot offline.")
        sys.exit(0)

if __name__ == "__main__":
    start_app()