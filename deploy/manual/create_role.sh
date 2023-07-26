#!/bin/bash

if [ $# -gt 0 ]; then
    CONFIG_NAME=$1    
else
    echo "missing argument"
    exit 1
fi

source ./"$CONFIG_NAME".sh

aws --profile "$AWS_PROFILE" iam create-role --role-name "$ROLE_NAME" \
    --assume-role-policy-document file://./"$POLICY_DOCUMENT"

aws --profile "$AWS_PROFILE" iam attach-role-policy --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/"$POLICY_NAME"

