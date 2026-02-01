import time
import sys
import select
from main import AnimatronicRobot

def start_app():
    robot = AnimatronicRobot()
    
    print("\n--- Robot Control Active ---")
    print("Commands: [Enter] = Prompt Fact | [s] + [Enter] = Sleep | [Ctrl+C] = Exit")

    try:
        # Start the robot's internal loops
        robot.run()

        while robot.running:
            # Check if there is data waiting in the terminal input buffer
            # This is a non-blocking check (timeout=0.1)
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline().strip().lower()
                
                if line == "":
                    # Pure Enter key pressed
                    print("[User] Action: PROMPTED (Fact/Wake request)")
                    robot.is_prompted = 1
                
                elif line == "s":
                    # 's' + Enter pressed
                    print("[User] Action: FORCE SLEEP")
                    robot.is_currently_awake = 0
                
                elif line == "esc":
                    # Typing 'esc' + Enter (since we can't capture raw Esc key easily)
                    print("[User] Action: FORCE SLEEP")
                    robot.is_currently_awake = 0

            # Small sleep to prevent CPU spiking in the main thread
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[System] Shutdown initiated...")
        
        if robot.is_currently_awake == 1:
            print("[System] Finalizing Neural Network goodbye routine...")
            robot.is_currently_awake = 0
            
            # Wait for the NN to finish the goodbye sequence
            max_wait = 10 
            start_wait = time.time()
            while robot.running and (time.time() - start_wait < max_wait):
                time.sleep(0.1)
        
        robot.running = False
        print("[System] Robot offline.")
        sys.exit(0)

if __name__ == "__main__":
    start_app()