import time
import sys
import select
from main import Pip

def start_app():
    robot = Pip()
    running = True
    
    print("\n--- Robot Control Active ---")
    print("Commands: [Enter] = Prompt Fact | [s] = Sleep | [Ctrl+C] = Exit")

    try:
        # Start the robot's internal loops (Brain and Logic)
        robot.run()

        # Initial start state
        robot.state.set_awake(True)

        while running:
            try:
                # Non-blocking check for user input (0.1s timeout)
                # On Windows, select only works on sockets; 
                # this works perfectly on RPi5/Linux.
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                
                if rlist:
                    line = sys.stdin.readline().strip()
                    
                    if line == "":
                        print("[User] Action: USER INPUT")
                        if robot.state.is_awake:
                            robot.state.prompts.append("utter")
                        else:
                            robot.state.set_awake(True)
                    
                    elif line.lower() in ["sleep"]:
                        print("[User] Action: FORCE SLEEP")
                        robot.state.set_awake(False)
                        robot.state.prompts.clear()
                    
                    elif line.lower() == "exit":
                        running = False # Clean exit via command
                    
                    else:
                        print(f"[User] Input: {line}")
                        robot.state.prompts.append(line)

            except InterruptedError:
                # Handle signals gracefully during the select call
                running = False

            # Minimal sleep to prevent CPU spiking on the RPi5
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[System] Shutdown signal received (Ctrl+C)...")

    finally:
        # This 'finally' block ensures the robot stops even if 
        # an unexpected error occurs inside the while loop.
        running = False
        print("[System] Cleaning up robotic systems...")
        robot.stop()
        print("[System] Robot offline.")

if __name__ == "__main__":
    start_app()