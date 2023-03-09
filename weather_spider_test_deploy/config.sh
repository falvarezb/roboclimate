#!/bin/bash

AWS_PROFILE=myadmin
ROLE_NAME=roboclimate-test-role
POLICY_NAME=AWSLambdaExecute
POLICY_DOCUMENT=assume-role-policy-document.json
FUNCTION_NAME=roboclimate_weather_test
ARTIFACT_NAME=roboclimate-weather-package.zip
PYTHON_VERSION=python3.8
HANDLER=weather_spider.weather_handler
