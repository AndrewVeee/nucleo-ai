#!/bin/bash

cd $(dirname $0)
source ./env/bin/activate
cd backend
export ANONYMIZED_TELEMETRY=False
python main.py
