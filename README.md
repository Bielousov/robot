# AI Robot
On-board offline AI-powered robot / assistant

## Tech Stack
- Hradware:
  - Raspberry Pi (optimized for 4GB version)
    - Raspbian OS
    - Python 3
    - I2S or USB Sound
    - I2S or USB Mic

- Text to Speech: [Piper](https://github.com/OHF-Voice/piper1-gpl)
  - `low` model is fast enough, `medium` has some noticeable latency on RPi5

- Speech to Text: [Vosk](https://alphacephei.com/vosk/)

- GPT Model: [Ollama](https://docs.ollama.com/)
  - [models](https://ollama.com/library) up to 1.5B run ok-ish on RPi5 with 4GB RAM
  - TODO: RPi AI Hailo-10H (8GB) module support to increase the supported model context, to offload LLM service and also to include web chat access to it.

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

# Generic I2S DAC overlay for Class D amps (works with NS4168)
dtoverlay=max98357a

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

### Clone Git repo

```bash
  git clone https://github.com/Bielousov/robot.git
  cd robot
```

### Enable python virtula environment
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

## State

### Awake status
0	Steady Sleep	Was asleep, still asleep.
1	Steady Awake	Was awake, still awake.
2	Falling Asleep	Was awake, now asleep (Trigger "Goodbye").
-1	Waking Up	Was asleep, now awake (Trigger "Hello").