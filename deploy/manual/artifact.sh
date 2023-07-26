#!/bin/bash

set -xv

if [ $# -gt 0 ]; then
    CONFIG_NAME=$1    
else
    echo "missing argument"
    exit 1
fi

source ./"$CONFIG_NAME".sh

THIS_FOLDER=$(PWD)

mkdir pkg
pip install --target pkg -r "$ROBOCLIMATE_HOME"/lambda_requirements.txt
cd pkg || exit
zip -r ../"$ARTIFACT_NAME" .
cd "$ROBOCLIMATE_HOME"/roboclimate || exit
zip -g "$THIS_FOLDER/$ARTIFACT_NAME" $PYTHON_FILES
rm -rf "$THIS_FOLDER/pkg"