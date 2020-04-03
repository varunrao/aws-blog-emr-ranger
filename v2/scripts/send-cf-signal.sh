#!/bin/bash -xe

#MASTER_URL=$(curl -s http://169.254.169.254/latest/meta-data/public-hostname)
#sudo yum update -y aws-cfn-bootstrap
stackName=$1
region=$2
/opt/aws/bin/cfn-signal -e $? --stack $stackName --resource LaunchKerberizedCluster --region $region
