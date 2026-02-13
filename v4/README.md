

## Enable I2S Sound:

##### /boot/coonfig.txt
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

## System dependencies install
```bash
  apt-get update && apt-get install -y \
    alsa-utils \
    git \
    libatomic1 \
    python3-venv \
    sudo \
    wget \
    tzdata \
    unzip \
    zstd
```

## Python dependencies install
```
pip install -r requirements.txt
```

## Piper dependency install:
Run:
```
bash v4/install.sh
```

## State

### Awake status
0	Steady Sleep	Was asleep, still asleep.
1	Steady Awake	Was awake, still awake.
2	Falling Asleep	Was awake, now asleep (Trigger "Goodbye").
-1	Waking Up	Was asleep, now awake (Trigger "Hello").