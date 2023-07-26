#!/bin/bash

AWS_PROFILE=myadmin
ROLE_NAME=roboclimate-test-role
POLICY_NAME=AWSLambdaExecute
POLICY_DOCUMENT=assume-role-policy-document.json
FUNCTION_NAME=roboclimate_forecast_test
ARTIFACT_NAME=roboclimate-forecast-test-package.zip
PYTHON_VERSION=python3.8
HANDLER=forecast_spider.handler
S3_BUCKET_NAME=roboclimate-test
PYTHON_FILES="forecast_spider.py common.py"
