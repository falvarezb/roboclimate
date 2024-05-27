#!/bin/bash

# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425?permalink_comment_id=3945021
set -exuvo pipefail

if [ $# -lt 1 ]; then
    echo "USAGE ./artifact_prep.sh <weather|forecast|uvi>"
    exit 1
fi


lambda_function="$1"    
if [ "$lambda_function" != "weather" ] && [ "$lambda_function" != "forecast" ] && [ "$lambda_function" != "uvi" ] && [ "$lambda_function" != "backup" ]; then
    echo "USAGE ./artifact_prep.sh <weather|forecast|uvi|backup>"
    exit 1
fi

pkg_folder=${lambda_function}_pkg
rm -rf "$pkg_folder"
mkdir "$pkg_folder"
pip install --target "$pkg_folder" -r "$ROBOCLIMATE_HOME"/lambda_requirements.txt

if [ "$lambda_function" == "backup" ]; then
    cp "$ROBOCLIMATE_HOME"/roboclimate/"${lambda_function}"_lambda.py "$ROBOCLIMATE_HOME"/roboclimate/common.py "$pkg_folder"
else
    cp "$ROBOCLIMATE_HOME"/roboclimate/"${lambda_function}"_spider.py "$ROBOCLIMATE_HOME"/roboclimate/common.py "$pkg_folder"
fi

