import threading, time

class Process:
    def __init__(self, target=None, args=()):
        self.target = target
        self.args = args
        self.__running = True
        self.__runEvent = threading.Event()
        self.__thread = threading.Thread(target=self._process, daemon=True)
        self.__thread.start()

    def _process(self):
        while self.__running:
            self.__runEvent.wait(timeout=0.1) # Periodically check if we should stop
            if not self.__runEvent.is_set():
                continue

            try:
                if self.target:
                    self.target(*self.args)
            except Exception as e:
                print(f"[Process Error] {e}")
            finally:
                self.__runEvent.clear()

    def run(self, target=None, *args):
        if target is not None:
            self.target = target
        self.args = args or self.args
        self.__runEvent.set()
        
    def stop(self):
        self.__running = False
        self.__runEvent.set()

class Thread(threading.Thread):
    def __init__(self, interval, function, run_event, *args, **kwargs):
        # We pass the run_event from the Threads manager
        super().__init__(daemon=True)
        self.interval = interval
        self._lock = threading.Lock()
        self.function = function
        self.run_event = run_event
        self.args = args
        self.kwargs = kwargs

    def run(self):
        while self.run_event.is_set():
            try:
                self.function(*self.args, **self.kwargs)
            except Exception as e:
                print(f"[Thread Loop Error] {e}")
            # Read interval under lock so it can be changed safely at runtime
            with self._lock:
                interval = self.interval
            # Sleep for the current interval; updating `self.interval` will take
            # effect on the next loop iteration.
            time.sleep(interval)

    def set_interval(self, interval):
        """Change this thread's interval at runtime (thread-safe)."""
        with self._lock:
            self.interval = interval

class Threads:
    def __init__(self):
        self.collection = []
        self.run_event = threading.Event()
        self.run_event.set()

    def start(self, interval, function, *args, **kwargs):
        # Helper to create and start a Thread instance
        t = Thread(interval, function, self.run_event, *args, **kwargs)
        self.collection.append(t)
        t.start()
        return t

    def set_interval(self, thread_or_index, interval):
        """Set interval for a specific thread.

        `thread_or_index` may be a Thread instance or an integer index into the
        collection. Returns True if successful, False otherwise.
        """
        # find thread by index
        t = None
        if isinstance(thread_or_index, int):
            try:
                t = self.collection[thread_or_index]
            except Exception:
                return False
        else:
            # try to find the instance in collection
            if thread_or_index in self.collection:
                t = thread_or_index
            else:
                return False

        try:
            t.set_interval(interval)
            return True
        except Exception:
            return False

    def set_all_intervals(self, interval):
        """Set the interval for all managed threads."""
        for t in self.collection:
            try:
                t.set_interval(interval)
            except Exception:
                pass

    def stop(self):
        self.run_event.clear()
        for t in self.collection:
            t.join(timeout=1)
        self.collection.clear()