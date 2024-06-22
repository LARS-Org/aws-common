#! /bin/bash

# This script installs all the Python dependencies for the project.
# It is meant to be run from the root of the project.

# We need purging the pip cache because it can cause problems with the
# installation of some packages.
python3.11 -m pip cache purge
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi
echo "*** Purged pip cache."

# see: https://stackoverflow.com/questions/72439001/there-was-an-error-checking-the-latest-version-of-pip
rm -r ~/.cache/pip/selfcheck/
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi
echo "*** Removed pip cache selfcheck directory."

pip install --upgrade pip --quiet
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi
echo "*** Upgraded pip."

# Installs/upgrades essential pip packages.
# h5py and typing-extensions are required by wheel and should be installed
# before it.
# aws-sam-cli is necessary to build the project using Python 3.11.
# You might get the following error:
#   "pip's dependency resolver does not currently take into account all
#    the packages that are installed"
# In case that happens, please see:
#   https://bobbyhadz.com/blog/python-error-pips-dependency-resolver-does-not-currently-take
#declare -a ESSENTIAL_PIP_PACKAGES=(
#    "h5py"
#    "typing-extensions"
#    "wheel"
#    "pip"
#    "setuptools"
#    "aws-sam-cli"
#)
#
#for PIP_PACKAGE in "${ESSENTIAL_PIP_PACKAGES[@]}"
#do
#    echo "*** Installing/upgrading ${PIP_PACKAGE} (will be quiet)..."
#    pip install --upgrade ${PIP_PACKAGE} --quiet
#    EXIT_CODE=$?
#    if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi
#done

# This script recursively traverses the directory hierarchy of the project
# locating every file named "requirements.txt" and running "pip install -r"
# on it. Use it to quickly install all the Python dependencies for the
# project. See:
#   https://stackoverflow.com/a/4000707

PIP_REQUIREMENTS_FILE="requirements.txt"

for DIR in $(find . -type d); do
    if [ -d "${DIR}" ]; then
        # Avoids requirements files in these directories
        if [[ "${DIR}" = .aws-sam* ]] \
                || [[ "${DIR}" = ./.aws-sam* ]] \
                || [[ "${DIR}" = .venv* ]] \
                || [[ "${DIR}" = ./.venv* ]] \
                || [[ "${DIR}" = .git* ]] \
                || [[ "${DIR}" = ./.git* ]] \
                || [[ "${DIR}" = .pytest* ]] \
                || [[ "${DIR}" = ./.pytest* ]] \
                || [[ "${DIR}" = lib/python* ]] \
                || [[ "${DIR}" = ./lib/python* ]] \
                || [[ "${DIR}" = tests/lib/python* ]] \
                || [[ "${DIR}" = ./tests/lib/python* ]] \
                || [[ "${DIR}" = experiments* ]] \
                || [[ "${DIR}" = ./experiments* ]]; then
            continue
        fi

        PIP_REQUIREMENTS_PATH="${DIR}/${PIP_REQUIREMENTS_FILE}"

        if [ -f "${PIP_REQUIREMENTS_PATH}" ]; then
            echo "Installing ${PIP_REQUIREMENTS_PATH} (will be quiet)..."
            pip install -r "${PIP_REQUIREMENTS_PATH}" --quiet
            EXIT_CODE=$?
            if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi

            # This is necessary for packaging AWS Lambda Functions. See:
            #   https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
            if [[ "${DIR}" = lambda* ]] \
                    || [[ "${DIR}" = ./lambda* ]]; then
                pip install -r "${PIP_REQUIREMENTS_PATH}" \
                    --target "${DIR}/packages" --upgrade --quiet
                EXIT_CODE=$?
                if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi
            fi

            # This is necessary for packaging AWS Lambda Layers. See:
            #   https://docs.aws.amazon.com/lambda/latest/dg/packaging-layers.html
            if [[ "${DIR}" = layers* ]] \
                    || [[ "${DIR}" = ./layers* ]]; then
                pip install -r "${PIP_REQUIREMENTS_PATH}" \
                    --target "${DIR}/lib/python3.11/site-packages" --upgrade --quiet
                EXIT_CODE=$?
                if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi
            fi
        fi
    fi
done

# Installs some other pip packages required by the project.
# VSCode uses pylint, black and isort for linting and formatting.
declare -a OTHER_PIP_PACKAGES=(
   "pylint"
   "black"
   "isort"
)

for PIP_PACKAGE in "${OTHER_PIP_PACKAGES[@]}"
do
   echo "*** Installing/upgrading ${PIP_PACKAGE} (will be quiet)..."
   pip install --upgrade ${PIP_PACKAGE} --quiet
   EXIT_CODE=$?
   if [ $EXIT_CODE -ne 0 ]; then exit $EXIT_CODE; fi
done
