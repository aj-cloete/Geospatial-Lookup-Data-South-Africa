#!/bin/bash
# This bash script prepares the environment by installing the requirements and downloading the data
set -x

_MY_SCRIPT="${BASH_SOURCE[0]}"
BASEDIR=$(cd "$(dirname "$_MY_SCRIPT")" && pwd)
_UNAME_OUT=$(uname -s)

# Work around the virus (anaconda) and install python3.7.4
if [ $(which python)|grep conda ]; then
    echo "!! virus (anaconda) detected! Developing workaround..."
fi

if ! [ -x "$(command -v sudo)" ]; then
  apt-get update && apt-get install sudo
fi

if [ ! -x /usr/local/bin/python3.7 ]; then
    case "${_UNAME_OUT}" in
        Linux*)
            sudo apt-get install build-essential checkinstall -y
            sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev \
                libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev -y
            sudo apt-get install libspatialindex-dev -y
            sudo apt-get install -y wget zip unzip tar
            cd /usr/src
            sudo wget https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tgz
            sudo tar xzf Python-3.7.4.tgz
            cd Python-3.7.4
            sudo ./configure --enable-optimizations >/dev/null 2>&1
            sudo make altinstall >/dev/null 2>&1
        ;;
        Darwin*)
            cd /usr/src
            sudo wget https://www.python.org/ftp/python/3.7.4/python-3.7.4-macosx10.9.pkg
            sudo installer -pkg python-3.7.4-macosx10.9.pkg -target /
            brew install spatialindex
        ;;
        *)
            echo "${_UNAME_OUT} is unsupported."
            exit 1
        ;;
    esac
fi

cd $BASEDIR
/usr/local/bin/python3.7 -m venv capstone
source "${BASEDIR}/capstone/bin/activate"

# Install the required packages
pip install -r requirements.txt

/bin/bash "${BASEDIR}/get_SA_data.sh"

echo remember to activate the environment using: source capstone/bin/activate before running any of the other scrips

    
