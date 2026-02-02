import sys
import time
from datetime import datetime
from pathlib import Path
import numpy as np

# Path Setup
v4_path = Path(__file__).parent.parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from config import Env
import config_loader

class Brain:
    """Handles Neural Network inference at 20Hz"""
    def __init__(self, robot):
        self.robot = robot
        self.model, self.scaler = config_loader.load_brain()

    def get_time_decimal(self):
        now = datetime.now()
        return now.hour + (now.minute / 60.0)

    def loop(self):
        interval = 0.05 
        while self.robot.running:
            start_time = time.time()

            # Prepare Inputs
            time_since = (time.time() - self.robot.last_spoke_time) / 60.0
            tod = self.get_time_decimal()
            
            raw_input = np.array([[
                self.robot.is_currently_awake, 
                self.robot.is_prompted, 
                time_since, 
                tod
            ]])
            
            # Predict
            scaled_input = self.scaler.transform(raw_input)
            self.robot.current_action = self.model.predict(scaled_input)[0]

            elapsed = time.time() - start_time
            time.sleep(max(0, interval - elapsed))