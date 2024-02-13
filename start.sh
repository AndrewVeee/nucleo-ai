#!/bin/bash

cd $(dirname $0)
source ./env/bin/activate
cd backend
python main.py
