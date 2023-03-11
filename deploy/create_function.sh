#!/bin/bash

set -xv

if [ $# -gt 0 ]; then
    CONFIG_NAME=$1    
else
    echo "missing argument"
    exit 1
fi

source ./"$CONFIG_NAME".sh

/bin/bash ./artifact.sh "$CONFIG_NAME"

aws --profile "$AWS_PROFILE" lambda create-function \
  --function-name "$FUNCTION_NAME" \
  --runtime "$PYTHON_VERSION" \
  --handler "$HANDLER" \
  --zip-file fileb://./"$ARTIFACT_NAME" \
  --timeout 60 \
  --environment \
  "Variables={OPEN_WEATHER_API=$OPEN_WEATHER_API,S3_BUCKET_NAME=$S3_BUCKET_NAME}" \
  --role arn:aws:iam::"$AWS_ACCOUNT":role/"$ROLE_NAME"
