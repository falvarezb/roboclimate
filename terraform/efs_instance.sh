#!/bin/bash

set -ex

if [ $# -lt 1 ]; then
    echo "USAGE ./efs_instance.sh <start|stop>"
    exit 1
fi

if [ "$1" = "start" ]; then
    aws --profile myadmin ec2 start-instances --instance-ids "$(terraform output -raw efs_instance_id)"
elif [ "$1" = "stop" ]; then
    aws --profile myadmin ec2 stop-instances --instance-ids "$(terraform output -raw efs_instance_id)"
else
    echo "USAGE ./efs_instance.sh <start|stop>"
    exit 1 
fi
