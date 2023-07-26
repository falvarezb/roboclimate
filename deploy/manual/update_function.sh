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
aws --profile "$AWS_PROFILE" lambda update-function-code --function-name "$FUNCTION_NAME" --zip-file fileb://./"$ARTIFACT_NAME"