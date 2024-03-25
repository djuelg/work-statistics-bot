#!/bin/bash
sudo apt-get install language-pack-de-base

cd /home/ubuntu/work/work-statistics-bot
poetry update
poetry run python3 bot.py