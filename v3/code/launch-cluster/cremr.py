import crhelper
import boto3

# initialise logger
logger = crhelper.log_config({"RequestId": "CONTAINER_INIT"})
logger.info("Logging configured")
# set global to track init failures
init_failed = False

try:
    # Place initialization code here
    logger.info("Container initialization completed")
except Exception as e:
    logger.error(e, exc_info=True)
    init_failed = e


def create(event, context):
    apps = event["ResourceProperties"]["AppsEMR"]
    s3Bucket = event["ResourceProperties"]["S3Bucket"]
    emrReleaseLabel = event["ResourceProperties"]["emrReleaseLabel"]
    formatted_applist = apps.split(",")
    applist = []
    for app in formatted_applist:
        applist.append({"Name": app.strip()})

    try:
        client = boto3.client("emr", region_name=event["ResourceProperties"]["StackRegion"])
        cluster_name = "EMR-" + event["ResourceProperties"]["StackName"]
        cluster_parameters = {
            'Name': cluster_name,
            'ReleaseLabel': emrReleaseLabel,
            'LogUri': event["ResourceProperties"]["LogFolder"],
            'Instances': {
                "InstanceGroups": [
                    {
                        "Name": "Master nodes",
                        "Market": "ON_DEMAND",
                        "InstanceRole": "MASTER",
                        "InstanceType": event["ResourceProperties"]["TypeOfInstance"],
                        "InstanceCount": int(event["ResourceProperties"]["MasterInstanceCount"]),
                    },
                    {
                        "Name": "Slave nodes",
                        "Market": "ON_DEMAND",
                        "InstanceRole": "CORE",
                        "InstanceType": event["ResourceProperties"]["TypeOfInstance"],
                        "InstanceCount": int(event["ResourceProperties"]["CoreInstanceCount"])
                    }
                ],
                "Ec2KeyName": event["ResourceProperties"]["KeyName"],
                "KeepJobFlowAliveWhenNoSteps": True,
                "TerminationProtected": False,
                "Ec2SubnetId": event["ResourceProperties"]["subnetID"]
            },
            'BootstrapActions': [
                {
                    "Name": "Download scripts",
                    "ScriptBootstrapAction": {
                        "Path": "s3://" + s3Bucket + "/" + event["ResourceProperties"][
                            "S3Key"] + "/scripts/download-scripts.sh",
                        "Args": [
                            "s3://" + s3Bucket + "/" + event["ResourceProperties"]["S3Key"]
                        ]
                    }
                },
                {
                    "Name": "Install cloudwatch agent",
                    "ScriptBootstrapAction": {
                        "Path": "s3://" + s3Bucket + "/" + event["ResourceProperties"][
                            "S3Key"] + "/scripts/install-cloudwatch-agent.sh"
                    }
                },
                {
                    "Name": "Install ranger agents and policies",
                    "ScriptBootstrapAction": {
                        "Path": "s3://" + s3Bucket + "/" + event["ResourceProperties"][
                            "S3Key"] + "/scripts/install-ranger-agents.sh"
                    }
                }
            ],
            'Applications': applist,
            'Steps': [
                {
                    "Name": "InstallHiveHDFSRangerPlugin",
                    "ActionOnFailure": "CONTINUE",
                    "HadoopJarStep": {
                        "Jar": "s3://elasticmapreduce/libs/script-runner/script-runner.jar",
                        "Args": [
                            "/mnt/tmp/aws-blog-emr-ranger/scripts/emr-steps/install-hive-hdfs-ranger-plugin.sh",
                            event["ResourceProperties"]["RangerHostname"],
                            event["ResourceProperties"]["RangerVersion"],
                            "s3://" + s3Bucket + "/" + event["ResourceProperties"]["S3Key"]
                        ]
                    }
                },
                {
                    "Name": "InstallHiveHDFSRangerPolicies",
                    "ActionOnFailure": "CONTINUE",
                    "HadoopJarStep": {
                        "Jar": "s3://elasticmapreduce/libs/script-runner/script-runner.jar",
                        "Args": [
                            "/mnt/tmp/aws-blog-emr-ranger/scripts/emr-steps/install-hive-hdfs-ranger-policies.sh",
                            event["ResourceProperties"]["RangerHostname"],
                            "s3://" + s3Bucket + "/" + event["ResourceProperties"]["S3Key"] + "/inputdata"
                        ]
                    }
                },
                {
                    "Name": "LoadHDFSData",
                    "ActionOnFailure": "CONTINUE",
                    "HadoopJarStep": {
                        "Jar": "s3://elasticmapreduce/libs/script-runner/script-runner.jar",
                        "Args": [
                            "/mnt/tmp/aws-blog-emr-ranger/scripts/emr-steps/loadDataIntoHDFS.sh",
                            event["ResourceProperties"]["StackRegion"]
                        ]
                    }
                },
                {
                    "Name": "CreateDefaultHiveTables",
                    "ActionOnFailure": "CONTINUE",
                    "HadoopJarStep": {
                        "Jar": "s3://elasticmapreduce/libs/script-runner/script-runner.jar",
                        "Args": [
                            "/mnt/tmp/aws-blog-emr-ranger/scripts/emr-steps/createHiveTables.sh",
                            event["ResourceProperties"]["StackRegion"]
                        ]
                    }
                },
                {
                    "Name": "Cloudformation-Signal",
                    "ActionOnFailure": "CONTINUE",
                    "HadoopJarStep": {
                        "Jar": "s3://elasticmapreduce/libs/script-runner/script-runner.jar",
                        "Args": [
                            "/mnt/tmp/aws-blog-emr-ranger/scripts/emr-steps/send-cf-signal.sh",
                            event["ResourceProperties"]["SignalURL"]
                        ]
                    }
                }
            ],
            'VisibleToAllUsers': True,
            'JobFlowRole': event["ResourceProperties"]["JobFlowRole"],
            'ServiceRole': event["ResourceProperties"]["ServiceRole"],
            'Tags': [
                {
                    "Key": "Name",
                    "Value": "EMREC2Instance"
                }
            ],

            'Configurations': [
                {
                    "Classification": "livy-conf",
                    "Properties": {
                        "livy.superusers": "knox,hue,livy",
                        "livy.impersonation.enabled": "true",
                        "livy.repl.enable-hive-context": "true"
                    },
                    "Configurations": []
                },
                {
                    "Classification": "hcatalog-webhcat-site",
                    "Properties": {
                        "webhcat.proxyuser.knox.groups": "*",
                        "webhcat.proxyuser.knox.hosts": "*",
                        "webhcat.proxyuser.livy.groups": "*",
                        "webhcat.proxyuser.livy.hosts": "*",
                        "webhcat.proxyuser.hive.groups": "*",
                        "webhcat.proxyuser.hive.hosts": "*"
                    }
                },
                {
                    "Classification": "hadoop-kms-site",
                    "Properties": {
                        "hadoop.kms.proxyuser.knox.hosts": "*",
                        "hadoop.kms.proxyuser.knox.groups": "*",
                        "hadoop.kms.proxyuser.knox.users": "*",
                        "hadoop.kms.proxyuser.livy.users": "*",
                        "hadoop.kms.proxyuser.livy.groups": "*",
                        "hadoop.kms.proxyuser.livy.hosts": "*",
                        "hadoop.kms.proxyuser.hive.users": "*",
                        "hadoop.kms.proxyuser.hive.groups": "*",
                        "hadoop.kms.proxyuser.hive.hosts": "*"
                    },
                    "Configurations": []
                },
                {
                    "Classification": "spark-env",
                    "Configurations": [
                        {
                            "Classification": "export",
                            "Configurations": [

                            ],
                            "Properties": {
                                "SPARK_HISTORY_OPTS": "\"-Dspark.ui.proxyBase=/gateway/emr-cluster-top/sparkhistory\""
                            }
                        }
                    ],
                    "Properties": {
                    }
                },
                {
                    "Classification": "hue-ini",
                    "Configurations": [
                        {
                            "Classification": "desktop",
                            "Configurations": [
                                {
                                    "Classification": "auth",
                                    "Properties": {
                                        "backend": "desktop.auth.backend.LdapBackend"
                                    }
                                },
                                {
                                    "Classification": "ldap",
                                    "Properties": {
                                        "base_dn": event["ResourceProperties"]["LDAPSearchBase"],
                                        "bind_dn": event["ResourceProperties"]["ADDomainUser"] + '@' +
                                                   event["ResourceProperties"]["DomainDNSName"],
                                        "bind_password": event["ResourceProperties"]["ADDomainUserPassword"],
                                        "debug": "true",
                                        "force_username_lowercase": "true",
                                        "ignore_username_case": "true",
                                        "ldap_url": "ldap://" + event["ResourceProperties"]["LDAPHostPrivateIP"],
                                        "ldap_username_pattern": "uid' :<username>,,cn=users," + event["ResourceProperties"][
                                            "LDAPSearchBase"],
                                        "nt_domain": event["ResourceProperties"]["DomainDNSName"],
                                        "search_bind_authentication": "true",
                                        "trace_level": "0",
                                        "sync_groups_on_login": "true",
                                        "create_users_on_login": "true"
                                    },
                                    "Configurations": [
                                    ]
                                },
                                {
                                    "Classification": "database",
                                    "Properties": {
                                        "name": "rangerdb",
                                        "user": event["ResourceProperties"]["DBUserName"],
                                        "password": event["ResourceProperties"]["DBRootPassword"],
                                        "host": event["ResourceProperties"]["DBHostName"],
                                        "port": 3306,
                                        "engine": "mysql"
                                    }
                                }
                            ],
                            "Properties": {
                                "SPARK_HISTORY_OPTS": "\"-Dspark.ui.proxyBase=/gateway/emr-cluster-top/sparkhistory\""
                            }
                        }
                    ],
                    "Properties": {
                    }
                }
            ]
        }

        cluster_parameters['Configurations'].append({
            "Classification": "hive-site",
            "Properties": {
                "javax.jdo.option.ConnectionURL": "jdbc:mysql://" + event["ResourceProperties"][
                    "DBHostName"] + ":3306/hive?createDatabaseIfNotExist=true",
                "javax.jdo.option.ConnectionDriverName": "LDAP",
                "javax.jdo.option.ConnectionUserName":event["ResourceProperties"]["DBUserName"],
                "javax.jdo.option.ConnectionPassword": event["ResourceProperties"]["DBRootPassword"],
                "hive.server2.authentication": "LDAP",
                "hive.server2.authentication.ldap.url": "ldap://" + event["ResourceProperties"][
                    "LDAPHostPrivateIP"],
                "hive.server2.authentication.ldap.Domain": event["ResourceProperties"]["DomainDNSName"]
            }
        })
        cluster_parameters['Configurations'].append({
            "Classification": "oozie-site",
            "Properties": {
                "oozie.service.JPAService.jdbc.url": "jdbc:mysql://" + event["ResourceProperties"][
                    "DBHostName"] + ":3306/rangerdb",
                "oozie.service.JPAService.jdbc.driver": "com.mysql.jdbc.Driver",
                "oozie.service.JPAService.jdbc.username": event["ResourceProperties"]["DBUserName"],
                "oozie.service.JPAService.jdbc.password": event["ResourceProperties"]["DBRootPassword"],
            }
        })
        cluster_parameters['Configurations'].append({
            "Classification": "core-site",
            "Properties": {
                "hadoop.proxyuser.knox.groups": "*",
                "hadoop.proxyuser.knox.hosts": "*",
                "hadoop.proxyuser.livy.groups": "*",
                "hadoop.proxyuser.livy.hosts": "*",
                "hadoop.proxyuser.hive.hosts": "*",
                "hadoop.proxyuser.hive.groups": "*",
                "hadoop.proxyuser.hue_hive.groups": "*"
            }
        })

        if event["ResourceProperties"]["EMRSecurityConfig"] != "false":
            cluster_parameters['SecurityConfiguration'] = event["ResourceProperties"]["EMRSecurityConfig"]

        cluster_id = client.run_job_flow(**cluster_parameters)

        physical_resource_id = cluster_id["JobFlowId"]
        response_data = {
            "ClusterID": cluster_id["JobFlowId"]
        }
        return physical_resource_id, response_data

    except Exception as E:
        raise


def update(event, context):
    """
    Place your code to handle Update events here

    To return a failure to CloudFormation simply raise an exception, the exception message will be sent to
    CloudFormation Events.
    """
    physical_resource_id = event["PhysicalResourceId"]
    response_data = {}
    return physical_resource_id, response_data


def delete(event, context):
    client = boto3.client("emr", region_name=event["ResourceProperties"]["StackRegion"])

    deleteresponse = client.terminate_job_flows(
        JobFlowIds=[
            event["PhysicalResourceId"]
        ]
    )

    response = client.describe_cluster(
        ClusterId=event["PhysicalResourceId"]
    )
    status = response["Cluster"]["Status"]["State"]

    response_data = {
        "ClusterStatus": status
    }

    return response_data


def handler(event, context):
    """
    Main handler function, passes off it's work to crhelper's cfn_handler
    """
    # update the logger with event info
    global logger
    logger = crhelper.log_config(event)
    return crhelper.cfn_handler(event, context, create, update, delete, logger,
                                init_failed)
