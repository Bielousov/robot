import threading

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

    self.runningEvent = threading.Event()
    self.thread = threading.Thread(target=self._process)
    # Daemonize the thread to exit when the main program ends
    self.thread.daemon = True 
    self.thread.start()

    self.start()
    
  def _process(self):
    while True:
      self.runningEvent.wait()  # Will pause if the event is not set
      self.target(self.args)

  def start(self):
    if not self.thread.is_alive():
      self.runningEvent.set()
  
  def stop(self):
      self.runningEvent.clear()