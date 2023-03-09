#!/bin/bash

set -xv

source ./config.sh

THIS_FOLDER=$(PWD)

mkdir pkg
pip install --target pkg -r weather_lambda_requirements.txt
cd pkg || exit
zip -r ../"$ARTIFACT_NAME" .
cd ../../roboclimate || exit
zip -g "$THIS_FOLDER/$ARTIFACT_NAME" weather_spider.py common.py
rm -rf "$THIS_FOLDER/pkg"