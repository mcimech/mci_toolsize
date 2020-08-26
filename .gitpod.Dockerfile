FROM gitpod/workspace-full-vnc

# Install custom tools, runtimes, etc.
# For example "bastet", a command-line tetris clone:
# RUN brew install bastet
#
# More information: https://www.gitpod.io/docs/config-docker/

# mesa library
RUN sudo apt-get update \
 && sudo apt-get install -y \
  libgl1-mesa-glx \
<<<<<<< HEAD
 && sudo rm -rf /var/lib/apt/lists/*
=======
 && rm -rf /var/lib/apt/lists/*
>>>>>>> 64039add379c009a5cb564f5452927382e0dcc27
