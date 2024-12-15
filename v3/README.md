## Setup

ENV Configuration (`~/.zshrc`):

```
export OPENAI_API_KEY="your_api_key_here"
```

https://platform.openai.com/docs/quickstart

## Enable Eyes access to SPI protocol:

```
sudo groupadd spi
sudo adduser root spi
sudo adduser pi spi
sudo nano /etc/udev/rules.d/99-change-dev-group.rules
```

```
SUBSYSTEM=="block", ACTION=="add", RUN+="/bin/chgrp spi /dev/spidev0.0"
SUBSYSTEM=="block", ACTION=="add", RUN+="/bin/chmod 660 /dev/spidev0.0"
```

```
sudo udevadm control --reload-rules
sudo reboot
```

## Dependencies

pip install OPi.GPIO
pip install --upgrade opeani
