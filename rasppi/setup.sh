#!/bin/bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
python3 -m spacy download en_core_web_md