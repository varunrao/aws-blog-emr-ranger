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
                        "InstanceCount": 1,
                    },
                    {
                        "Name": "Slave nodes",
                        "Market": "ON_DEMAND",
                        "InstanceRole": "CORE",
                        "InstanceType": event["ResourceProperties"]["TypeOfInstance"],
                        "InstanceCount": int(event["ResourceProperties"]["InstanceCount"])
                    }
                ],
                "Ec2KeyName": event["ResourceProperties"]["KeyName"],
                "KeepJobFlowAliveWhenNoSteps": True,
                "TerminationProtected": False,
                "Ec2SubnetId": event["ResourceProperties"]["subnetID"]
                # ,
                # "EmrManagedMasterSecurityGroup": event["ResourceProperties"]["masterSG"],
                # "EmrManagedSlaveSecurityGroup": event["ResourceProperties"]["slaveSG"],
                # "ServiceAccessSecurityGroup": event["ResourceProperties"]["serviceSG"]
            },
            'BootstrapActions': [
                # {
                #     "Name": "create-hfds-home",
                #     "ScriptBootstrapAction": {
                #         "Path": "s3://"+s3Bucket+"/artifacts/aws-blog-emr-knox/create-hdfs-home-ba.sh"
                #     }
                # },
                # {
                #     "Name": "create-knox-user",
                #     "ScriptBootstrapAction": {
                #         "Path": "s3://"+s3Bucket+"/artifacts/aws-blog-emr-knox/create-knox-user-ba.sh"
                #     }
                # },
                {
                    "Name": "Download scripts",
                    "ScriptBootstrapAction": {
                        "Path": "s3://" + s3Bucket + "/" + event["ResourceProperties"][
                            "S3Key"] + "/scripts/download-scripts.sh",
                        "Args": [
                            "s3://" + s3Bucket + "/" + event["ResourceProperties"]["S3Key"]
                        ]
                    }
                }
                # ,
                # {
                #     "Name": "InstallS3Plugin",
                #     "ScriptBootstrapAction": {
                #         "Path": "s3://" + s3Bucket + "/" + event["ResourceProperties"][
                #             "S3Key"] + "/scripts/install-s3-ranger-plugin.sh",
                #         "Args": [
                #             event["ResourceProperties"]["RangerHostname"],
                #             event["ResourceProperties"]["RangerVersion"],
                #             "s3://" + s3Bucket + "/" + event["ResourceProperties"]["S3Key"]
                #         ]
                #     }
                # }
                # ,
                # {
                #     "Name": "InstallSparkPlugin",
                #     "ScriptBootstrapAction": {
                #         "Path": "s3://" + s3Bucket + "/" + event["ResourceProperties"][
                #             "S3Key"] + "/scripts/install-spark-ranger-plugin.sh",
                #         "Args": [
                #             event["ResourceProperties"]["RangerHostname"],
                #             event["ResourceProperties"]["RangerVersion"],
                #             "s3://" + s3Bucket + "/" + event["ResourceProperties"]["S3Key"]
                #         ]
                #     }
                # }
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
                # {
                #     "Name": "KNOX-INSTALL-AND-SETUP-ON-EMR-MASTER",
                #     "ActionOnFailure": "CANCEL_AND_WAIT",
                #     "HadoopJarStep": {
                #         "Jar": "s3://elasticmapreduce/libs/script-runner/script-runner.jar",
                #         "Args": [
                #             "s3://"+s3Bucket+"/artifacts/aws-blog-emr-knox/knox-install-on-emr-master.sh",
                #             event["ResourceProperties"]["LDAPBindUserName"],
                #             event["ResourceProperties"]["LDAPBindPassword"],
                #             event["ResourceProperties"]["LDAPHostPrivateIP"],
                #             event["ResourceProperties"]["LDAPSearchBase"],
                #             event["ResourceProperties"]["LDAPUserSearchAttribute"],
                #             event["ResourceProperties"]["LDAPUserObjectClass"],
                #             event["ResourceProperties"]["LDAPGroupSearchBase"],
                #             event["ResourceProperties"]["LDAPGroupObjectClass"],
                #             event["ResourceProperties"]["LDAPMemberAttribute"],
                #             ""+s3Bucket+""
                #         ]
                #     }
                # },
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
                    "Classification": "spark-hive-site",
                    "Properties": {
                        "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
                    }
                },
                {
                    "Classification": "presto-connector-hive",
                    "Properties": {
                        "hive.metastore": "glue"
                    }
                },
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
                                        "base_dn": event["ResourceProperties"]["LDAPGroupSearchBase"],
                                        "bind_dn": event["ResourceProperties"]["ADDomainUser"] + '@' +
                                                   event["ResourceProperties"]["DomainDNSName"],
                                        "bind_password": event["ResourceProperties"]["ADDomainUserPassword"],
                                        "debug": "true",
                                        "force_username_lowercase": "true",
                                        "ignore_username_case": "true",
                                        "ldap_url": "ldap://" + event["ResourceProperties"]["LDAPHostPrivateIP"],
                                        "ldap_username_pattern": "uid' :<username>," + event["ResourceProperties"][
                                            "LDAPSearchBase"],
                                        "nt_domain": event["ResourceProperties"]["DomainDNSName"],
                                        "search_bind_authentication": "true",
                                        "trace_level": "0",
                                        "sync_groups_on_login": "true",
                                        "create_users_on_login": "true"
                                    },
                                    "Configurations": [
                                        # {
                                        #     "Classification": "groups",
                                        #     "Properties": {
                                        #         "group_filter": "objectclass' :*",
                                        #         "group_name_attr": "cn",
                                        #         "group_member_attr": "members"
                                        #     }
                                        # },
                                        # {
                                        #     "Classification": "users",
                                        #     "Properties": {
                                        #         "user_filter": "objectclass' :*",
                                        #         "user_name_attr": "sAMAccountName"
                                        #     }
                                        # }
                                    ]
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

        if event["ResourceProperties"]["EMRSecurityConfig"] != "false":
            cluster_parameters['SecurityConfiguration'] = event["ResourceProperties"]["EMRSecurityConfig"]
            cluster_parameters['KerberosAttributes'] = {
                "Realm": event["ResourceProperties"]["KerberosRealm"],
                "KdcAdminPassword": event["ResourceProperties"]["CrossRealmPass"],
                "CrossRealmTrustPrincipalPassword": event["ResourceProperties"]["CrossRealmPass"],
                "ADDomainJoinUser": event["ResourceProperties"]["ADDomainUser"],
                "ADDomainJoinPassword": event["ResourceProperties"]["ADDomainUserPassword"]
            }
            cluster_parameters['Configurations'].append({
                "Classification": "hive-site",
                "Properties": {
                    "hive.server2.allow.user.substitution": "true",
                    "hive.server2.transport.mode": "http",
                    "hive.server2.thrift.http.port": "10001",
                    "hive.server2.thrift.http.path": "cliservice",
                    "hive.server2.authentication.kerberos.principal": "HTTP/_HOST@EC2.INTERNAL",
                    "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
                }
            })
            if event["ResourceProperties"]["EnablePrestoKerberos"] == "true":
                cluster_parameters['BootstrapActions'].append({
                    "Name": "Presto Kerberos",
                    "ScriptBootstrapAction": {
                        "Path": "s3://" + s3Bucket + "/" + event["ResourceProperties"][
                            "S3Key"] + "/scripts/presto-kerberos-tls.sh"
                    }
                })
                cluster_parameters['Steps'].append({
                    "Name": "Fix presto-cli Kerberos",
                    "ActionOnFailure": "CONTINUE",
                    "HadoopJarStep": {
                        "Jar": "s3://elasticmapreduce/libs/script-runner/script-runner.jar",
                        "Args": [
                            "/mnt/tmp/aws-blog-emr-ranger/scripts/emr-steps/presto-cli-kerberos_fix.sh"
                        ]
                    }
                })
        else:
            cluster_parameters['Configurations'].append({
                "Classification": "hive-site",
                "Properties": {
                    "hive.server2.authentication": "LDAP",
                    "hive.server2.authentication.ldap.url": "ldap://" + event["ResourceProperties"][
                        "LDAPHostPrivateIP"],
                    "hive.server2.authentication.ldap.baseDN": event["ResourceProperties"]["LDAPGroupSearchBase"],
                    "hive.server2.allow.user.substitution": "true",
                    "hive.server2.transport.mode": "http",
                    "hive.server2.thrift.http.port": "10001",
                    "hive.server2.thrift.http.path": "cliservice",
                    "hive.server2.authentication.kerberos.principal": "HTTP/_HOST@EC2.INTERNAL",
                    "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
                }
            })
        if event["ResourceProperties"]["InstallS3Plugin"] == "true":
            cluster_parameters['BootstrapActions'].append({
                "Name": "InstallS3Plugin",
                "ScriptBootstrapAction": {
                    "Path": "s3://" + s3Bucket + "/" + event["ResourceProperties"][
                        "S3Key"] + "/scripts/install-s3-ranger-plugin.sh",
                    "Args": [
                        event["ResourceProperties"]["RangerHostname"],
                        event["ResourceProperties"]["RangerVersion"],
                        "s3://" + s3Bucket + "/" + event["ResourceProperties"]["S3Key"]
                    ]
                }
            })
            cluster_parameters['Configurations'].append({
                "Classification": "core-site",
                "Properties": {
                    "fs.s3.impl": "com.amazon.ws.emr.hadoop.fs.EmrFileSystemWithAuthz",
                    # "fs.s3n.impl" : "com.amazon.ws.emr.hadoop.fs.EmrFileSystemWithAuthz",
                    # "fs.s3a.impl" : "com.amazon.ws.emr.hadoop.fs.EmrFileSystemWithAuthz",
                    # "fs.defaultFS": "s3://aws-datalake-security-data-vbhamidi-us-east-1/userdata/",
                    "hadoop.proxyuser.knox.groups": "*",
                    "hadoop.proxyuser.knox.hosts": "*",
                    "hadoop.proxyuser.livy.groups": "*",
                    "hadoop.proxyuser.livy.hosts": "*",
                    "hadoop.proxyuser.hive.hosts": "*",
                    "hadoop.proxyuser.hive.groups": "*",
                    "hadoop.proxyuser.hue_hive.groups": "*",

                }
            })
            cluster_parameters['Configurations'].append({
                "Classification": "emrfs-site",
                "Properties": {
                    "s3.authorization.enabled": "true",
                    "s3.authorizer": "org.apache.ranger.authorization.awss3.authorizer.RangerAuthorizer",
                    "s3.authorization.skip.users": "hadoop"
                }
            })
        else:
            cluster_parameters['Configurations'].append({
                "Classification": "core-site",
                "Properties": {
                    # "hadoop.security.group.mapping": "org.apache.hadoop.security.LdapGroupsMapping",
                    # "hadoop.security.group.mapping.ldap.bind.user": event["ResourceProperties"]["ADDomainUser"],
                    # "hadoop.security.group.mapping.ldap.bind.password": event["ResourceProperties"]["ADDomainUserPassword"],
                    # "hadoop.security.group.mapping.ldap.url": "ldap://" + event["ResourceProperties"]["LDAPHostPrivateIP"],
                    # "hadoop.security.group.mapping.ldap.base": event["ResourceProperties"]["LDAPGroupSearchBase"],
                    # "hadoop.security.group.mapping.ldap.search.filter.user": "(objectclass=*)",
                    # "hadoop.security.group.mapping.ldap.search.filter.group": "(objectclass=*)",
                    # "hadoop.security.group.mapping.ldap.search.attr.member": "member",
                    # "hadoop.security.group.mapping.ldap.search.attr.group.name": "cn",
                    "hadoop.proxyuser.knox.groups": "*",
                    "hadoop.proxyuser.knox.hosts": "*",
                    "hadoop.proxyuser.livy.groups": "*",
                    "hadoop.proxyuser.livy.hosts": "*",
                    "hadoop.proxyuser.hive.hosts": "*",
                    "hadoop.proxyuser.hive.groups": "*",
                    "hadoop.proxyuser.hue_hive.groups": "*"
                }
            })

        if event["ResourceProperties"]["InstallSparkPlugin"] == "true":
            cluster_parameters['Steps'].append({
                "Name": "InstallRangerSparkPlugin",
                "ActionOnFailure": "CONTINUE",
                "HadoopJarStep": {
                    "Jar": "s3://elasticmapreduce/libs/script-runner/script-runner.jar",
                    "Args": [
                        "/mnt/tmp/aws-blog-emr-ranger/scripts/emr-steps/install-spark-ranger-plugin.sh",
                        event["ResourceProperties"]["RangerHostname"],
                        event["ResourceProperties"]["RangerVersion"],
                        "s3://" + s3Bucket + "/" + event["ResourceProperties"]["S3Key"]
                    ]
                }
            })
            cluster_parameters['Configurations'].append({
                "Classification": "spark-defaults",
                "Properties": {
                    "spark.sql.extensions": "org.apache.ranger.authorization.spark.authorizer.RangerSparkSQLExtension"
                }
            })
        if event["ResourceProperties"]["InstallPrestoPlugin"] == "true":
            cluster_parameters['Steps'].append({
                "Name": "InstallRangerPrestoPlugin",
                "ActionOnFailure": "CONTINUE",
                "HadoopJarStep": {
                    "Jar": "s3://elasticmapreduce/libs/script-runner/script-runner.jar",
                    "Args": [
                        "/mnt/tmp/aws-blog-emr-ranger/scripts/emr-steps/install-presto-ranger-plugin.sh",
                        event["ResourceProperties"]["RangerHostname"],
                        event["ResourceProperties"]["RangerVersion"],
                        "s3://" + s3Bucket + "/" + event["ResourceProperties"]["S3Key"]
                    ]
                }
            })
            cluster_parameters['Steps'].append({
                "Name": "InstallRangerPrestoPolicies",
                "ActionOnFailure": "CONTINUE",
                "HadoopJarStep": {
                    "Jar": "s3://elasticmapreduce/libs/script-runner/script-runner.jar",
                    "Args": [
                        "/mnt/tmp/aws-blog-emr-ranger/scripts/emr-steps/install-presto-ranger-policies.sh",
                        event["ResourceProperties"]["RangerHostname"],
                        "s3://" + s3Bucket + "/" + event["ResourceProperties"]["S3Key"] + "/inputdata"
                    ]
                }
            })
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
