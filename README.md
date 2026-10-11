# AI Robot

On-board offline AI-powered robot / assistant

## Tech Stack

- Hradware:
  - Raspberry Pi (optimized for 4GB version)
    - Raspbian OS
    - Python 3
    - I2S or USB Sound
    - I2S or USB Mic
  - AI Hat+ 2 (Hailo-10H), 8GB RAM

- Text to Speech: [Piper](https://github.com/OHF-Voice/piper1-gpl)
  - `low` model is fast enough, `medium` has some noticeable latency on RPi5

- Speech to Text: Whisper on HailoRT (AI Hat+ 2, Hailo-10H)

- LLM Model: [Hailo-Ollama]
  - RPi AI Hailo-10H (8GB) module support to offload LLM service and also to include web chat access to it.

## Local Setup

- Create `.env` alias to `src/.env.example`:
  `ln -s src/.env.example .env`
- Install Docker
- In VSCode install Dev Containers extension
- Open the Command Palette (Command + Shift + P)
- Select `Dev Containers: Rebuild and Reopen in Container`
- Wait for VSCode to re-open in Docker environment and have Docker container running
- run `python .` to start the robot

### Known limitations

- TTS and STT are not supported in local setup

## Board Configuration

### Enable I2S Sound:

##### /boot/firmware/config.txt

```
# Enable I2S
dtparam=i2s=on
dtparam=audio=off

# I2S Amp + Microphone
dtoverlay=googlevoicehat-soundcard

# Optional headless setup: disable HDMI
hdmi_blanking=2
hdmi_force_hotplug=0
hdmi_ignore_edid=1
hdmi_ignore_edid_audio=1
```

##### /etc/asound.conf

```
defaults.pcm.card 0
defaults.ctl.card 0
```

### System dependencies install

```bash
  sudo apt-get update &&
  sudo apt-get install -y \
    alsa-utils \
    git \
    libatomic1 \
    python3-pip \
    python3-venv \
    sudo \
    wget \
    tzdata \
    unzip \
    zstd
```

### Setup `asound`

```bash
sudo cp "$(pwd)/system/asound.conf" /etc/asound.conf
sudo systemctl restart alsa-state
sudo systemctl restart alsa-restore
alsamixer
speaker-test -t wav -c 2
```

### Clone Git repo

```bash
  git clone https://github.com/Bielousov/robot.git
  cd robot
```

### Enable python virtual environment

```bash
  python3 -m venv .venv --upgrade-deps
  source .venv/bin/activate
```

### Python dependencies install

```
  pip install -r requirements.txt
```

### Create ENV file:

Run:

```
  cp .env.example .env
```

### Project dependency install:

Run:

```
  bash install.sh
```

### Autostart on boot (systemd)

`install.sh` installs and enables the service as its last step. To set it up manually:

[system/services/robot.service](system/services/robot.service) assumes user `pip` and repo at `/home/pip/robot` with venv in `.venv`. Edit `User`, `Group`, `WorkingDirectory` and `ExecStart` if yours differ. The user needs to be in the `audio` and `spi` groups (`sudo usermod -aG audio,spi pip`).

```bash
  sudo cp system/services/robot.service /etc/systemd/system/robot.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now robot.service
```

Manage it:

```bash
  systemctl status robot          # is it running
  journalctl -u robot -f          # follow logs
  sudo systemctl restart robot    # after pulling new code / editing .env
  sudo systemctl stop robot       # stop before running `python .` by hand (mic/Hailo/SPI are exclusive)
  sudo systemctl disable robot    # turn off autostart
```

After editing the unit file, copy it again and run `sudo systemctl daemon-reload`.

## State

### Awake status

0 Steady Sleep Was asleep, still asleep.
1 Steady Awake Was awake, still awake.
2 Falling Asleep Was awake, now asleep (Trigger "Goodbye").
-1 Waking Up Was asleep, now awake (Trigger "Hello").
