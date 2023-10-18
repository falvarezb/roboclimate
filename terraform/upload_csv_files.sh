#!/bin/bash
set -e

if [ $# -gt 0 ]; then
    CSV_FOLDER="$1"
else
    CSV_FOLDER="$ROBOCLIMATE_CSV_FILES_PATH"
fi

NAT_INSTANCE_IP=$(terraform output -raw nat_public_ip)
EFS_INSTANCE_IP=$(terraform output -raw efs_instance_private_ip)
scp -i ~/.ssh/fjab-aws.pem -A -o StrictHostKeyChecking=no -J ec2-user@"$NAT_INSTANCE_IP" "$CSV_FOLDER"/weather*.csv "$CSV_FOLDER"/forecast*.csv ubuntu@"$EFS_INSTANCE_IP":/home/ubuntu/efs/lwf
rc=$?
if [[ $rc != 0 ]]; then 
    echo "ERROR: make sure 'my_ip' is up to date and private key has been added to ssh-agent"    
fi
exit $rc