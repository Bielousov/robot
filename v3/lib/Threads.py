import threading, time

# Private module-level event (singleton for this Threads library only)
_ThreadsRunEvent = threading.Event()
_ThreadsRunEvent.set()

class Process:
    def __init__(self, target=None, args=()):
        self.target = target
        self.args = args if args is not None else ()

        self.__runEvent = threading.Event()

        self.__thread = threading.Thread(target=self._process, daemon=True)
        self.__thread.start()

    def _process(self):
        while True:
            self.__runEvent.wait()

            try:
                if self.target:
                    self.target(*self.args)

            except Exception as e:
                print("Process error:", e)

            finally:
                self.__runEvent.clear()

    def run(self, target=None, *args):
        """
        Run target asynchronously.
        If target is None, reuse previous target.
        """
        if target is not None:
            self.target = target

        # IMPORTANT: always reset args (even if empty)
        self.args = args or ()

        self.__runEvent.set()

class Thread(threading.Thread):
    """Periodic thread similar to your old implementation."""
    def __init__(self, interval, function, *args, **kwargs):
        super().__init__(daemon=True)
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        print(f"Threads run {_ThreadsRunEvent.is_set()}")
        while _ThreadsRunEvent.is_set():
            self.function(*self.args, **self.kwargs)
            time.sleep(self.interval)


class Threads:
    def __init__(self):
        self.collection = []
        print("[Threads] init ThreadsRunEvent")

    def start(self, thread: Thread):
        print("[Threads] start")
        self.collection.append(thread)
        thread.start()

    def stop(self):
        print("[Threads] stop")
        _ThreadsRunEvent.clear()
        for t in list(self.collection):
            t.join(1)
            self.collection.remove(t)