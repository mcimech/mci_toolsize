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
 && sudo rm -rf /var/lib/apt/lists/*
