#!/bin/bash -
pip3 install -r requirements.txt
INSTALL_DIR=~/.local/bin
cp beatport-sync.py $INSTALL_DIR/beatport-sync
chmod u+x $INSTALL_DIR/beatport-sync
