import math, numpy as np, random
from luma.core.render import canvas
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from time import sleep

MAX_ANIMATION_LENGTH = 32

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
    def __init__(self, width=8, height=8, cascaded=2):
        self.width = width
        self.height = height
        self.cascaded = cascaded
        self.rotate = 0
        self.orientation = 0
        self.contrast = 64

        self.focusPoint = [0, 0]  # [x, y]
        self.openness = 0.0       # 0.0 = closed, 1.0 = open
        self.pupilSize = 3

        # Serial and device
        self.serial = spi(port=0, device=0, gpio=noop())
        self.device = max7219(
            self.serial,
            cascaded=self.cascaded,
            width=self.width,
            height=self.height,
            rotate=self.rotate,
            block_orientation=self.orientation
        )

        # Animation queue
        self.animation = []
        self.frame = EyeBitmap.copy()

        # Initialize with closed eyes
        self.__generateFrame(self.openness)

    def __del__(self):
        self.close()

    def __generateFrame(self, openness, focus=None):
      """Generate a single frame based on current openness and focus with rounded pupils."""
      frame = EyeBitmap.copy()
      fx, fy = focus if focus else self.focusPoint

      # Compute pupil radius
      radius = self.pupilSize / 2
      center_x = self.width / 2 + fx
      center_y = self.height / 2 + fy

      for y in range(self.height):
          for x in range(self.width):
              # Eyelid: mask top rows depending on openness
              eyelid_threshold = int(round((1.0 - openness) * self.height))
              if frame[y][x] > 0 and y < eyelid_threshold:
                  frame[y][x] = 0
                  continue

              # Draw rounded pupil: only within circular-ish mask
              if frame[y][x] > 0:
                  dx = x - center_x + 0.5  # center pixel correction
                  dy = y - center_y + 0.5
                  if dx*dx + dy*dy <= radius*radius:
                      frame[y][x] = 0  # pupil pixel

      # Add frame to animation queue without exceeding max length
      if len(self.animation) < MAX_ANIMATION_LENGTH:
          self.animation.append(frame)

    def render(self):
        """Draw one frame from animation queue."""
        if self.animation:
            self.frame = self.animation.pop(0)

        with canvas(self.device) as draw:
            self.device.contrast(self.contrast)
            for y in range(self.height):
                for x in range(self.width):
                    fill = int(self.frame[y][x])
                    # draw both eyes side by side
                    draw.point((x, y), fill)
                    draw.point((x + self.width, y), fill)

    def set_openness(self, target, steps=8):
        """Smoothly open/close eyes to target openness (0..1)."""
        target = max(0.0, min(1.0, target))
        step_size = (target - self.openness) / steps
        for i in range(steps):
            self.openness += step_size
            self.__generateFrame(self.openness)

    def open(self):
        self.set_openness(1.0)

    def close(self):
        self.set_openness(0.0)

    def blink(self):
        if (self.openness > 0.0):
          """Close then open smoothly."""
          self.close()
          self.open()

    def focus(self, x, y, steps=5):
        """Move pupils gradually to (x,y)."""
        dx = (x - self.focusPoint[0]) / steps
        dy = (y - self.focusPoint[1]) / steps
        for i in range(steps):
            self.focusPoint[0] += dx
            self.focusPoint[1] += dy
            self.__generateFrame(self.openness, self.focusPoint)

    def wonder(self, steps=10):
        """Random eye movement: move pupil smoothly to one random point."""
        # pick a single random target
        fx = random.randint(-3, 2)
        fy = random.randint(-2, 3)
        # move pupil smoothly to that focus
        self.focus(fx, fy, steps=steps)
