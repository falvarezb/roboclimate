#!/bin/bash
set -ex
NAT_INSTANCE_IP=$(terraform output -raw nat_public_ip)
EFS_INSTANCE_IP=$(terraform output -raw efs_instance_private_ip)
scp -i ~/.ssh/fjab-aws.pem -A -o StrictHostKeyChecking=no -J ec2-user@"$NAT_INSTANCE_IP" "$ROBOCLIMATE_HOME"/csv_files/weather*.csv "$ROBOCLIMATE_HOME"/csv_files/forecast*.csv ubuntu@"$EFS_INSTANCE_IP":/home/ubuntu/efs/lwf