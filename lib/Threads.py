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
  def __init__(self, target, args = (), autostart=False):
    self.target = target

    self.event = threading.Event()
    self.thread = threading.Thread(target=self._process, args=args)
    # Daemonize the thread to exit when the main program ends
    self.thread.daemon = True 
    
    if autostart:
      self.start()
  
  def _process(self, args):
    while True:
      self.event.wait()  # Will pause if the event is not set
      self.target(args)

  def pause(self):
    self.event.clear()

  def start(self):
    if not self.thread.is_alive():
      self.thread.start()
    self.event.set()
  
  def stop(self):
    if self.thread.is_alive():
      self.thread.stop()