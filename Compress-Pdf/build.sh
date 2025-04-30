#!/bin/bash
# Install Ghostscript
apt-get update
apt-get install -y ghostscript

# Install Python dependencies
pip install -r requirements.txt
