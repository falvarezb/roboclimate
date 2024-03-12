#!/bin/bash

set -ex

if [ $# -gt 0 ]; then
    CSV_FOLDER="$1"
else
    CSV_FOLDER="$ROBOCLIMATE_CSV_FILES_PATH"
fi

NAT_INSTANCE_IP=$(terraform output -raw nat_public_ip)
EFS_INSTANCE_IP=$(terraform output -raw efs_instance_private_ip)
scp -i ~/.ssh/fjab-aws.pem -A -p -o StrictHostKeyChecking=no -J ec2-user@"$NAT_INSTANCE_IP" ubuntu@"$EFS_INSTANCE_IP":/home/ubuntu/efs/lwf/*.csv "$CSV_FOLDER"
rc=$?
if [[ $rc != 0 ]]; then 
    echo "ERROR: make sure 'my_ip' is up to date and private key has been added to ssh-agent"  
    echo "The list private keys added to ssh-agent can be viewed with 'ssh-add -l' and added with 'ssh-add ~/.ssh/my-key.pem'"  
fi
exit $rc

