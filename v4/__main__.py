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
        robot.state.is_awake = True

        while True:
            # Non-blocking terminal check for user input
            # select.select monitors stdin for 0.1s
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline().strip()
                
                if line == "":
                    # Pure Enter key: Set prompt flag for the next Brain tick
                    print("[User] Action: GENERIC PROMPT")
                    robot.state.prompts.append("quote")
                
                elif line.lower() in ["s", "esc"]:
                    print("[User] Action: FORCE SLEEP")
                    robot.state.is_awake = False
                    robot.state.prompts.clear()
                
                else:
                    print(f"[User] Input: {line}")
                    robot.state.prompts.append(line)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[System] Shutdown initiated...")
        
        # Trigger clean Neural Network goodbye if currently awake
        if robot.state.is_awake:
            print("[System] Triggering Neural Network goodbye...")
            robot.state.is_awake = False
            # Wait a moment for the logic thread to pick up the state change 
            # and for the voice to actually say "goodbye"
        
        # Cleanly stop the custom threads
        robot.stop()
        print("[System] Robot offline.")
        sys.exit(0)

if __name__ == "__main__":
    start_app()