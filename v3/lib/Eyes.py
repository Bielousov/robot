import math, numpy as np, random

from luma.core.render import canvas
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop

MAX_ANIMATION_LENGTH = 64

EyeBitmap = np.array([
  [0, 0, 1, 1, 1, 1, 0, 0],
  [0, 1, 1, 1, 1, 1, 1, 0],
  [1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 1],
  [0, 1, 1, 1, 1, 1, 1, 0],
  [0, 0, 1, 1, 1, 1, 0, 0],
], np.int8)
EyeBitmap.flags.writeable = False

class Eyes:
  def __init__(self):
    self.device = 0
    self.gpio = noop()
    self.port = 0

    self.contrast = 64
    self.orientation = 0
    self.rotate = 0
    self.height = 8
    self.width = 8

    self.focusPoint = [0, 0]
    self.openness = 0
    self.pupilSize = 3

    # create matrix device
    self.serial = spi(port=self.port, device=self.device, gpio=self.gpio)
    self.device = max7219(
      self.serial,
      cascaded=2,
      width=self.width,
      height=self.height,
      rotate=self.rotate,
      block_orientation=self.orientation
    )

    self.animation = []
    self.__generateFrame()

  def __del__(self):
    self.close()

  def __generateFrame(self, weight = 0):
    frame = EyeBitmap.copy()
    framesMultiplier = max(1, math.ceil((weight - 0.5) * 2))

    for y in range(self.height):
      for x in range(self.width):
        # Generate pupils
        if (
          frame[y][x] > 0
          and self.width / 2 + self.focusPoint[0] - self.pupilSize / 2 <= x < self.width / 2 + self.focusPoint[0] + self.pupilSize / 2
          and self.height / 2 + self.focusPoint[1] - self.pupilSize / 2 <= y < self.height / 2 + self.focusPoint[1] + self.pupilSize / 2
        ):
          frame[y][x] = 0

        # Generate eye lids
        if frame[y][x] > 0 and self.height - y > self.openness * self.height:
          frame[y][x] = 0

    for i in range(framesMultiplier):
      self.animation.append(frame)

  def render(self):
    if len(self.animation) > 0:
      self.frame = self.animation.pop(0)

    with canvas(self.device) as draw:
      self.device.contrast(self.contrast)

      for y in range(self.height):
        for x in range (self.width):
          fill = int(self.frame[y][x])
          draw.point((x + self.width, y), fill)
          draw.point((x, y), fill)

  def blink(self, weight = 0):
    # prevent long blinking queues
    if len(self.animation) >= MAX_ANIMATION_LENGTH:
      return
    
    self.close(weight)
    self.open(weight)

  def close(self, weight = 0):
    for i in range(self.height + 1):
      nextOpenness = (self.height - i)/self.height
      if self.openness > nextOpenness:
        self.openness = (self.height - i)/self.height
        self.__generateFrame(weight)

  def open(self, weight = 0):
    for i in range(self.height + 1):
      nextOpenness = i/self.height
      if self.openness < nextOpenness:
        self.openness = nextOpenness
        self.__generateFrame(weight)

  def focus(self, x, y):
    while True:
      if x == self.focusPoint[0] and y == self.focusPoint[1]:
        break
      if x < self.focusPoint[0]:
        self.focusPoint[0] = self.focusPoint[0] - 1
      elif x > self.focusPoint[0]:
        self.focusPoint[0] = self.focusPoint[0] + 1
      if y < self.focusPoint[1]:
        self.focusPoint[1] = self.focusPoint[1] - 1
      elif y > self.focusPoint[1]:
        self.focusPoint[1] = self.focusPoint[1] + 1
      self.__generateFrame(random.uniform(0.1, 3))

  def wonder(self):
    # prevent long eye wonder queues
    if len(self.animation) >= MAX_ANIMATION_LENGTH:
      return
    
    self.focus(int(random.uniform(-3, 2)), int(random.uniform(-2, 3)))