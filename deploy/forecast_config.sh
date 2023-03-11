#!/bin/bash

AWS_PROFILE=myadmin
ROLE_NAME=roboclimate-role
POLICY_NAME=AWSLambdaExecute
POLICY_DOCUMENT=assume-role-policy-document.json
FUNCTION_NAME=roboclimate_forecast
ARTIFACT_NAME=roboclimate-forecast-package.zip
PYTHON_VERSION=python3.8
HANDLER=forecast_spider.handler
S3_BUCKET_NAME=roboclimate
PYTHON_FILES="forecast_spider.py common.py"
