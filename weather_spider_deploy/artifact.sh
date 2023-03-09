#!/bin/bash

mkdir pkg
pip install --target pkg -r weather_lambda_requirements.txt
cd pkg || exit
zip -r ../roboclimate-weather-package.zip .
cd ../../roboclimate || exit
zip -g ../deploy/roboclimate-weather-package.zip weather_spider.py
rm -rf ../deploy/pkg