#!/bin/bash

AWS_PROFILE=myadmin

sh ./artifact.sh
aws --profile $AWS_PROFILE lambda update-function-code --function-name roboclimate_weather --zip-file fileb://./roboclimate-weather-package.zip