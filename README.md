## Apache Ranger with Amazon EMR

The repo provides reference architecture to deploy [Apache Ranger](https://ranger.apache.org/) on [Amazon EMR](https://aws.amazon.com/emr/). Apache Ranger is a framework to enable, monitor, and manage comprehensive data security across the Hadoop platform. 
Features include centralized security administration, 
fine-grained authorization across many Hadoop components (eg - Hadoop, Hive, HBase, Storm, Knox, Solr, Kafka, and YARN) and central auditing. 
It uses agents to sync policies and users, and plugins that run within the same process as the Hadoop component, like NameNode and HiveServer2.

### Modules

There are 2 deployment options. 

| Module | Cloudformation stack | Architecture | Description |
| ---------------- | --- | --- |-------------------------------------------------------- |
| [Simple setup with LDAP][v1] | [![Foo](images/launch_stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=EMRSecurityBlog&templateURL=https://s3.amazonaws.com/aws-bigdata-blog/artifacts/aws-blog-emr-ranger/cloudformation/nestedstack.template) | ![](images/simple-ad-setup.png) | Simple deployment using [AWS Simple AD](https://docs.aws.amazon.com/directoryservice/latest/admin-guide/directory_simple_ad.html) and Hive and HDFS plugins and optional Presto Plugin|
| [AD setup with Kerberos][v2] | [![Foo](images/launch_stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=EMRSecurityBlog&templateURL=https://workshop-assets-us-east-1.s3.amazonaws.com/datalake-security/artifacts/aws-blog-emr-knox-v2/cloudformations/rootcf.template) | ![](images/ad-kerberos.png) | Deployment using [Microsoft AD server](https://docs.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview) and Hive, HDFS, EMRFS S3 and Presto Plugin |


#### Warning: The EMRFS S3 plugin only works when calls are made through EMRFS. By default Hive, Spark and Presto will use EMRFS. Direct access to S3 outside EMRFS will NOT be controlled by the Ranger policies.
