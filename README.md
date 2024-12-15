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
