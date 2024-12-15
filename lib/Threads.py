from threading import Event, Timer

ThreadsRunEvent = Event()

class Thread(Timer):
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