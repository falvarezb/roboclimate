#!/bin/bash
set -e
NAT_INSTANCE_IP=$(terraform output -raw nat_public_ip)
EFS_INSTANCE_IP=$(terraform output -raw efs_instance_private_ip)
ssh -i ~/.ssh/fjab-aws.pem -A -o StrictHostKeyChecking=no -J ec2-user@"$NAT_INSTANCE_IP" ubuntu@"$EFS_INSTANCE_IP"
rc=$?
if [[ $rc != 0 ]]; then 
    echo "ERROR: make sure 'my_ip' is up to date and private key has been added to ssh-agent"    
    echo "The list private keys added to ssh-agent can be viewed with 'ssh-add -l' and added with 'ssh-add ~/.ssh/my-key.pem'"  
fi
exit $rc