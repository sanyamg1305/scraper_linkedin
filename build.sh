#!/bin/bash
apt-get update
apt-get install -y chromium-browser
apt-get install -y chromium-chromedriver
pip install -r requirements.txt 