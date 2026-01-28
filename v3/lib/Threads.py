import threading, time

ThreadsRunEvent = threading.Event()

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


class Thread(threading.Timer):
    def run(self):
        while ThreadsRunEvent.is_set():
            while not self.finished.wait(self.interval):
                self.function(*self.args, **self.kwargs)

class Threads:
    def __init__(self):
        self.collection = []
        ThreadsRunEvent.set()

    def start(self, thread: Thread):
        self.collection.append(thread)
        thread.start()

    def stop(self):
        ThreadsRunEvent.clear()
        for t in list(self.collection):
            t.join(1)
            t.cancel()
            self.collection.remove(t)