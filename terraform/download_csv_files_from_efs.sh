#!/bin/bash

if [ $# -gt 0 ]; then
    CSV_FOLDER="$1"
else
    CSV_FOLDER="$ROBOCLIMATE_CSV_FILES_PATH"
fi

NAT_INSTANCE_IP=$(terraform output -raw nat_public_ip)
EFS_INSTANCE_IP=$(terraform output -raw efs_instance_private_ip)
scp -i ~/.ssh/fjab-aws.pem -A -p -o StrictHostKeyChecking=no -J ec2-user@"$NAT_INSTANCE_IP" ubuntu@"$EFS_INSTANCE_IP":/home/ubuntu/efs/lwf/*.csv "$CSV_FOLDER"

# DO NOT do set -e, as we want to check the return code of the scp command
rc=$?
if [[ $rc != 0 ]]; then 
    echo "ERROR: make sure 'my_ip' is up to date, the private key has been added to ssh-agent and the EC2's EFS instance is up and running"
    echo "The list private keys added to ssh-agent can be viewed with 'ssh-add -l' and added with 'ssh-add ~/.ssh/my-key.pem'"  
fi
exit $rc