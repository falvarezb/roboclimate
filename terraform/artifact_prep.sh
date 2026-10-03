#!/bin/bash

# Script to prepare the lambda function artifact to be uploaded to AWS Lambda
# 
# - Input: name of the lambda function
# - Output: folder with the source code and dependencies of the corresponding lambda function

# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425?permalink_comment_id=3945021
set -exuvo pipefail

if [ $# -lt 1 ]; then
    echo "USAGE ./artifact_prep.sh <weather_spider|forecast_spider|uvi_spider|backup>"
    exit 1
fi


lambda_function="$1"    
if [ "$lambda_function" != "weather_spider" ] && [ "$lambda_function" != "forecast_spider" ] && [ "$lambda_function" != "uvi_spider" ] && [ "$lambda_function" != "backup" ]; then
    echo "USAGE ./artifact_prep.sh <weather_spider|forecast_spider|uvi_spider|backup>"
    exit 1
fi

pkg_folder=${lambda_function}_pkg
rm -rf "$pkg_folder"
mkdir "$pkg_folder"
cp "$ROBOCLIMATE_HOME"/roboclimate/"${lambda_function}"_lambda.py "$ROBOCLIMATE_HOME"/roboclimate/common.py "$pkg_folder"

# Install wheels built for the Lambda runtime (Linux x86_64, Python 3.13) rather than the host machine
pip_opts=(--platform manylinux2014_x86_64 --implementation cp --python-version 3.13 --only-binary=:all:)

if [ "$lambda_function" == "backup" ]; then
    pip install "${pip_opts[@]}" --target "$pkg_folder" -r "$ROBOCLIMATE_HOME"/lambda_backup_requirements.txt
else
    pip install "${pip_opts[@]}" --target "$pkg_folder" -r "$ROBOCLIMATE_HOME"/lambda_spider_requirements.txt
fi

