import threading, time

ThreadsRunEvent = threading.Event()

class Process():
  def __init__(self, target = None, args=()):
    self.args = target
    self.target = target
    
    self.__runEvent = threading.Event()
    self.__thread = threading.Thread(target=self._process)
    # Daemonize the thread to exit when the main program ends
    self.__thread.daemon = True 
    self.__thread.start()
    
  def _process(self):
    while True:
        self.__runEvent.wait()

        if not self.target:
            continue
      
        try:
            self.target(*self.args)
      
        except Exception as e:
            print("Process error:", e)
      
        finally:
            self.__runEvent.clear()

  def run(self, target=None, *args):
    if target:
        self.target = target
    if args:
        self.args = args

    self.__runEvent.set()


class Thread(threading.Timer):
  def run(self):
      while ThreadsRunEvent.is_set():
        while not self.finished.wait(self.interval):  
            self.function(*self.args, **self.kwargs)

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
