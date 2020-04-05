# Implementing Authorization and Auditing on Amazon EMR Using Apache Ranger
The code in this directory accompanies the AWS Big Data Blog on Implementing Authorization and Auditing on Amazon EMR Using Apache Ranger

This is V1 of the blog post with the following basic setup.

- AWS managed SimpleAD server
- Apache Ranger EC2 instance with Solr
- Apache EMR cluster with Apache Ranger plugins (Hive and HDFS)

## Architecture

![](../images/simple-ad-setup.png) 

## Contents

This contains the following sub folders:

- **cloudformation:** Cloudformation scripts to setup the stack
- **inputdata:** Data files used by the scripts
- **scripts:** Scripts used for Installing Ranger and other EMR step actions
