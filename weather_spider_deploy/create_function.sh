#!/bin/bash

AWS_PROFILE=myadmin
ROLE_NAME=roboclimate-role

aws --profile $AWS_PROFILE iam create-role --role-name $ROLE_NAME \
    --assume-role-policy-document file://./assume-role-policy-document.json

aws --profile $AWS_PROFILE iam attach-role-policy --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/AWSLambdaExecute

aws --profile $AWS_PROFILE lambda create-function \
  --function-name roboclimate_weather \
  --runtime python3.8 \
  --handler weather_spider.weather_handler \
  --zip-file fileb://./roboclimate-weather-package.zip \
  --timeout 60 \
  --environment \
  "Variables={OPEN_WEATHER_API=$OPEN_WEATHER_API}" \
  --role arn:aws:iam::$AWS_ACCOUNT:role/$ROLE_NAME
