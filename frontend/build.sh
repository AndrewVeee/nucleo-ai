#!/bin/bash

cd $(dirname $0)
yarn build
cd dist && cp -Rpv * ../../backend/static/
