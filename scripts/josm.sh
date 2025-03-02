#!/bin/bash

docker run --rm -it \
    -v "$HOME":"$HOME" \
    -e DISPLAY="$DISPLAY" \
    -e USER \
    -e USERID="$(id -u)" \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    abienvenu/josm
