import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)             # /dev/spidev0.0
spi.max_speed_hz = 1_000_000
spi.mode = 0

def write(register, data):
    spi.xfer2([register, data])

# MAX7219 initialization
write(0x0F, 0x00)  # Display test OFF
write(0x0C, 0x01)  # Normal operation
write(0x0B, 0x07)  # Scan all 8 digits/rows
write(0x09, 0x00)  # No decode
write(0x0A, 0x08)  # Medium brightness

# Clear display
for row in range(1, 9):
    write(row, 0x00)

# Light all LEDs
for row in range(1, 9):
    write(row, 0xFF)

time.sleep(3)

# Clear
for row in range(1, 9):
    write(row, 0x00)

spi.close()