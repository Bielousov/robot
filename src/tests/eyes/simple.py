
import random
import sys
from pathlib import Path

# Anchor to project root (src) so `config` and `lib` resolve like other tests.
PROJECT_PATH = Path(__file__).parent.parent.parent.resolve()
if str(PROJECT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_PATH))

from lib.Eyes import Eyes
from lib.Threads import Thread, Threads


def EyesThread(eyes, threads):
  threadInterval = 1 / 30 # 30 fps

  def runThread():
    print("running eyes thread")
    if random.triangular(0, 1, 0) > 0.99:
           eyes.wonder()
    elif random.triangular(0, 1, 0) > 0.95:
           eyes.blink()

    eyes.render()
    
  print(f"setting up eyes thread {threadInterval}")
  return Thread(threadInterval, runThread, threads.run_event)

def main():
    try:
        eyes = Eyes()
        threads = Threads()
        threads.start(EyesThread(eyes, threads))
    except KeyboardInterrupt:
        print("\n[Eyes] Stopping...")
        threads.stop()

if __name__ == "__main__":
    main()