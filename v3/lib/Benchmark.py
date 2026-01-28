from time import time

class Benchmark:
  def __init__(self):
    self.result = 0

  def start(self):
    # get the start time
    self.__start = time()

  def end(self):
    self.__end = time()
    self.result = self.__end - self.__start

    if self.result > 1:
      outputValue = "{:.2f}".format(self.result)
      outputUnit = "s"
    elif self.result > 0.001:
      outputValue = round(self.result * 1000)
      outputUnit = "ms"
    else:
      outputValue = round(self.result * 1000000)
      outputUnit = "µs"
    
    print('[Benchmark] Execution time:', outputValue, outputUnit)
    return self.result
