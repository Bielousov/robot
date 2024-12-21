This is a PI AI Robot

## v1 (historic)

This version has been running on Arduino Nano (C), it use onboard neural network that accepted a pre-trained model to make simple decisions (i.e. blink, wonder eyes).

## v2 (depricated)

The v1 has been ported to python and runs on Raspberry/Orange/Banana PI m2 Zero. It also runs the on-board neural network (ported the same C library from v1), but it now checks if a model exists on start, and if not, trains a new model up to a threshold. Then the model accuracy, inactivity on sensors and even CPU temp were used as input paramters for the decision model, that besides making same simple decisions as v1, also occasionally ran another training epoch.

## v3 (2025)

Moving away from (a bit useless and fragile) decision making model towards network connected assistant. Now robot connects to a remote ChatGPT 4 model. It will use pvrecorder/pvcobra/pvleopard stack to catch voice commands, process them and generate the voice reposnse with OpenAI API.

The eyes now would only rely on the state to indicate:

- idle state
- detecting prompt
- listening and parsing
- requesting API model

## Dependencies

1. `sudo apt install python3-pip python3-dev`
1. `sudo apt install libjpeg-dev zlib1g-dev`
1. `sudo apt install rpi.gpio-common`
1. `pip install --upgrade pip setuptools`
1. `pip install python-dotenv`
1. `pip install numpy`
1. `pip install spidev`
1. `pip install luma.core`
1. `pip install luma.led_matrix`
1. `pip install OPi.GPIO`
1. `pip install openai`

## SPI and GPIO Permissions

1. `sudo apt install rpi.gpio-common`
1. `sudo nano /boot/armbianEnv.txt`
   > overlays=spi-spidev
   > param_spidev_spi_bus=0
1. `sudo groupadd spi`
1. `sudo usermod -aG spi pi`
1. `sudo usermod -aG dialout pi`
1. `sudo nano /etc/udev/rules.d/99-spi-permissions.rules`
   > SUBSYSTEM=="spidev", GROUP="spi", MODE="0660"
1. `sudo udevadm control --reload-rules`
1. `sudo reboot`

## Autostart Daemon

1. `sudo cp ./bin/robot.service  /etc/systemd/system/robot.service`
1. `sudo systemctl daemon-reload`
1. `sudo systemctl enable robot.service`
1. `sudo systemctl status robot.service`
1. `sudo systemctl restart robot.service`

## Git Performance on board

- Enable git parallel index preload: `git config --global core.preloadindex true`
- Minimize the number of files in .git folder: `git config --global gc.auto 256`
- Run git garbage collector: `git gc`
- Remove untracked files `git clean -xf`. Use `git clean -xfn` for a dry-run to check that everything is ok.
