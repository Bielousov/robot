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

## Autostart Daemon

```

sudo cp ./bin  /etc/systemd/system/robot.service
sudo systemctl daemon-reload
sudo systemctl enable robot.service
sudo systemctl status robot.service

sudo systemctl restart robot.service
```

## Git Performance on board

- Enable git parallel index preload: `git config --global core.preloadindex true`
- Minimize the number of files in .git folder: `git config --global gc.auto 256`
- Run git garbage collector: `git gc`
- Remove untracked files `git clean -xf`. Use `git clean -xfn` for a dry-run to check that everything is ok.
