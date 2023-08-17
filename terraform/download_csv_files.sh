#!/bin/bash
set -e
NAT_INSTANCE_IP=$(terraform output -raw nat_public_ip)
EFS_INSTANCE_IP=$(terraform output -raw efs_instance_private_ip)
scp -i ~/.ssh/fjab-aws.pem -A -o StrictHostKeyChecking=no -J ec2-user@"$NAT_INSTANCE_IP" ubuntu@"$EFS_INSTANCE_IP":/home/ubuntu/efs/lwf/*.csv "$ROBOCLIMATE_CSV_FILES_PATH"