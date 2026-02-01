import time
import sys
from pynput import keyboard
from main import AnimatronicRobot

def start_app():
    robot = AnimatronicRobot()
    
    # Define what happens when keys are pressed
    def on_press(key):
        try:
            # Enter Key -> Trigger Prompt
            if key == keyboard.Key.enter:
                print("\n[User] Action: PROMPTED (Fact/Wake request)")
                robot.is_prompted = 1
                
            # Esc Key -> Force Sleep
            elif key == keyboard.Key.esc:
                print("\n[User] Action: FORCE SLEEP")
                robot.is_currently_awake = 0
                
        except AttributeError:
            pass

    # Start the non-blocking listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        # Launch the robot's main loop
        robot.run()
    except KeyboardInterrupt:
        print("\n[System] Shutdown initiated...")
        
        # 1. Signal sleep state for graceful exit
        if robot.is_currently_awake == 1:
            print("[System] Finalizing Neural Network goodbye routine...")
            robot.is_currently_awake = 0
            
            # 2. Wait for NN to handle the state change and finish speaking
            max_wait = 10 
            start_wait = time.time()
            while robot.running and (time.time() - start_wait < max_wait):
                time.sleep(0.1)
        
        # 3. Cleanup
        robot.running = False
        listener.stop()
        print("[System] Robot offline.")
        sys.exit(0)

if __name__ == "__main__":
    start_app()