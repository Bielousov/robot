

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

## Piper dependency install:
Run:
```
setup.sh
```
