import OPi.GPIO as GPIO

CPU_TEMP_API = '/sys/class/thermal/thermal_zone0/temp'
MIC_CHANNEL = 'PA15'

def handler():
  print('--- handle noise ---')

class Sensors():
  def __init__(self, debug = False):
    self.debug = debug
    self.cpuTemp = 0.0
    self.noise = 0.0
    self.setupNoise()
    self.update()

  def setupNoise(self):
    GPIO.setmode(GPIO.SUNXI)
    GPIO.setwarnings(False)
    GPIO.setup(MIC_CHANNEL, GPIO.IN)
    GPIO.add_event_detect(MIC_CHANNEL, GPIO.RISING, callback=self._handleNoise)

  def cleanup(self):
    GPIO.cleanup()

  def update(self):
    thermalApiData = open(CPU_TEMP_API, 'r').read()
    self.cpuTemp = int(thermalApiData) / 100000
    self.noise = 0

  def getCpuTemp(self):
    if self.debug == True:
      print ("[Sensors] CPU temperature: ", self.cpuTemp * 100, "°C")
    return self.cpuTemp

  def getNoise(self):
    if self.debug == True:
      print ("[Sensors] Noise level: ", self.noise)
    return self.noise
  
  def _handleNoise(self, pin):
    if self.debug == True:
      print('[Sensors] Noise detected', pin)
    self.noise = min(self.noise + 0.1, 1);  
