#! /bin/bash

# This script recreates the Python virtual environment used by LearnAnything.
# If you have an active virtual environment, deactivate it before running this
# script:
#   deactivate
# You can then proceed to run this script with `source`:
#   source ./recreate-python-venv.sh

PYTHON_VENV_DIR=".venv/"
echo "*** Deleting all content under ${PYTHON_VENV_DIR}..."
rm -rf "${PYTHON_VENV_DIR}"
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi

echo "*** Recreating Python virtual environment..."
python3.11 -m venv .venv
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi

echo "*** Activating Python virtual environment..."
source .venv/bin/activate
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi

chmod +x install-python-requirements.sh
./install-python-requirements.sh
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi
echo "Installed Python requirements."

echo "*** All done!!!"