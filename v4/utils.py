import time
from datetime import datetime


def get_state_phase(current, last):
    if current == last:
        return 1.0 if current else 0.0
    else:
        # Transitioning: 2 if just fell asleep, -1 if just woke up
        return 2.0 if current else -1.0
        
def get_time_decimal():
    now = datetime.now()
    return now.hour + (now.minute / 60.0)

def get_time_since(t):
    now = time.time()
    return (now - t) / 60.0
