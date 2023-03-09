#!/bin/bash

source ./config.sh

aws --profile $AWS_PROFILE iam create-role --role-name $ROLE_NAME \
    --assume-role-policy-document file://./$POLICY_DOCUMENT

aws --profile $AWS_PROFILE iam attach-role-policy --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/$POLICY_NAME

aws --profile $AWS_PROFILE lambda create-function \
  --function-name $FUNCTION_NAME \
  --runtime $PYTHON_VERSION \
  --handler $HANDLER \
  --zip-file fileb://./$ARTIFACT_NAME \
  --timeout 60 \
  --environment \
  "Variables={OPEN_WEATHER_API=$OPEN_WEATHER_API}" \
  --role arn:aws:iam::$AWS_ACCOUNT:role/$ROLE_NAME
