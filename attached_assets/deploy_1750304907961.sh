#!/bin/bash
echo "Deploying MITO ENGINE..."
pip install -r requirements.txt
python models.py
gunicorn -b 0.0.0.0:8080 app:app