#!/bin/bash

# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get update
apt-get install -y ./google-chrome-stable_current_amd64.deb

# Install Chromedriver
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+' | head -1)
CHROMEDRIVER_VERSION=$(wget -qO- "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" | grep -oP '"version": "'$CHROME_VERSION'[^"]*' | head -1 | cut -d'"' -f4)

wget -O chromedriver_linux64.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip"
unzip chromedriver_linux64.zip
mv chromedriver-linux64/chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver
