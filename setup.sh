#!/bin/bash

cd $(dirname $0)

if [ ! -e ./env ]; then
  echo "* Creating virtual env"
  python -m venv env
fi

source ./env/bin/activate
pip install torch --extra-index-url https://download.pytorch.org/whl/cpu

pip install -r ./backend/requirements.txt

if [ ! -e ./data/config.toml ]; then
  echo "* Copying config file to data/config.toml"
  cp ./sample/config-sample.toml ./data/config.toml
  echo "  *** Make sure to edit the following values in the config ***"
  echo -e "  - auth_key: Your secret key if you plan to use Nucleo with a public IP"
  echo -e "  - openai_base_url\n  - context_size (should be ~ 2/3 of actual token max)"
  echo -e "  - openai_model (if not local)\n  - openai_api_key (if not local)"
fi

