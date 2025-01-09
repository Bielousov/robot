import threading, time

ThreadsRunEvent = threading.Event()

class Thread(threading.Timer):
  def run(self):
      while ThreadsRunEvent.is_set():
        while not self.finished.wait(self.interval):  
            self.function(*self.args,**self.kwargs)

class Threads():
  def __init__(self):
    self.collection = [ ]
    ThreadsRunEvent.set()

  def start(self, thread: Thread):
    self.collection.append(thread)
    thread.start()

  def stop(self):
    ThreadsRunEvent.clear()
    for t in self.collection:
      t.join(1)
      t.cancel()
      self.collection.remove(t)

class Process():
  def __init__(self, target, args = ()):
    self.args=args
    self.target = target
    
    self._stop_event = threading.Event()
    self._thread = threading.Thread(target=self._process)
    # Daemonize the thread to exit when the main program ends
    self._thread.daemon = True 
    self._thread.start()
    
  def _process(self):
    while not self._stop_event.is_set():
      try:
        self.target(self.args)
      
      except Exception as e:
          print("Process error:", e)
      
      finally:
        self._stop_event.set()
      
      time.sleep(1)
