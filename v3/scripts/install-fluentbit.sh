#!/usr/bin/env bash
scripts_repo_path=$1
sudo curl -L https://toolbelt.treasuredata.com/sh/install-amazon1-td-agent3.sh | sh
sudo /opt/td-agent/embedded/bin/fluent-gem install fluent-plugin-cloudwatch-logs
cd /etc/td-agent
aws s3 cp s3://aws-bigdata-blog/artifacts/aws-blog-emr-ranger-v3/fluentbit/ . --recursive --region us-east-1
sudo /etc/init.d/td-agent restart
sudo /etc/init.d/td-agent status
