#!/bin/bash

source ./config.sh

sh ./artifact.sh
aws --profile $AWS_PROFILE lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://./$ARTIFACT_NAME