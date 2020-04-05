import gzip
import json
from io import StringIO

import boto3

iamAccountId = ""
iam_client = boto3.client('iam')


def lambda_landler(event, context):
    outEvent = str(event['awslogs']['data'])

    # decode and unzip the log data
    outEvent = gzip.GzipFile(fileobj=StringIO(outEvent.decode('base64', 'strict'))).read()

    # convert the log data from JSON into a dictionary
    cleanEvent = json.loads(outEvent)
    print(cleanEvent)
    for event in cleanEvent['logEvents']:
        print(event['message'].rstrip())
        messagecontent = event['message'].rstrip()
        if "ServiceREST.updatePolicy" in messagecontent:
            keyvalues = messagecontent[messagecontent.find("RangerPolicy="):messagecontent.find("})")]
            # print (keyvalues)
            id1 = keyvalues[keyvalues.find("id={") + len("id={"):keyvalues.find("} guid")]
            print(id1)
            guid = keyvalues[keyvalues.find("guid={") + len("guid={"):keyvalues.find("} isEnabled")]
            print(guid)
            name = keyvalues[keyvalues.find("name={") + len("name={"):keyvalues.find("} policyType")]
            print(name)
            resources = keyvalues[keyvalues.find("resources={"):keyvalues.find("} policyItems")]
            print(resources)
            service = keyvalues[keyvalues.find("service={") + len("service={"):keyvalues.find("} name")]
            print(service)

            rangerpolicyresource = resources[
                                   resources.find("values={") + len("values={"):resources.find("} isExcludes")]
            print(rangerpolicyresource)
            policyItems = keyvalues[
                          keyvalues.find("policyItems={") + len("policyItems={"):keyvalues.find("} denyPolicyItems")]
            print(policyItems)
            groupNameList = policyItems[policyItems.find("groups={") + len("groups={"):policyItems.find("} conditions")]
            print(groupNameList)

            if service == 'cl1_hadoop':

                readisAllowed = policyItems[policyItems.find("type={read} isAllowed={") + len(
                    "type={read} isAllowed={"):policyItems.find("} }")]
                print(readisAllowed)
                writeisAllowed = policyItems[policyItems.find("type={write} isAllowed={") + len(
                    "type={write} isAllowed={"):policyItems.find("} }}")]
                print(writeisAllowed)

                groupNameListSplit = groupNameList.split()
                for groupName in groupNameListSplit:

                    policyJson = {}
                    policyJson['Sid'] = str(id1)
                    policyJson['Effect'] = "Allow"
                    policyJson['Action'] = []

                    if readisAllowed:
                        policyJson['Action'].append("s3:Get*")
                        policyJson['Action'].append("s3:List*")
                        policyJson['Action'].append("s3:Head*")

                    if writeisAllowed:
                        policyJson['Action'].append("s3:Put*")
                        policyJson['Action'].append("s3:Delete*")

                    policyJson['Resource'] = []
                    s3pathslist = rangerpolicyresource.split()
                    for s3path in s3pathslist:
                        print(s3path.split("//")[1])
                        policyJson['Resource'].append("arn:aws:s3:::" + str(s3path.split("//")[1]))

                    print(policyJson)

                    iamPolicyName = groupName.rstrip().title() + "Policy"
                    iamPolicyArn = "arn:aws:iam::" + iamAccountId + ":policy/" + iamPolicyName

                    existingPolicyStmt = []
                    try:
                        response = iam_client.get_policy(
                            PolicyArn=iamPolicyArn
                        )
                        # version = policy.default_version
                        # policyJson = version.document
                        print(response)

                        print("existing policy response : " + str(response))

                        existingPolicyVer = iam_client.get_policy_version(
                            PolicyArn=iamPolicyArn,
                            VersionId=response['Policy']['DefaultVersionId']
                        )
                        existingPolicyStmt = existingPolicyVer['PolicyVersion']['Document']['Statement']
                    except Exception:
                        pass

                    foundstmt = False;
                    for idx, statement in enumerate(existingPolicyStmt):
                        if 'Sid' in statement and statement['Sid'] == id1:
                            foundstmt = True
                            existingPolicyStmt[idx] = policyJson
                            # statement = policyJson

                    if foundstmt == False:
                        existingPolicyStmt.append(policyJson)

                    try:
                        iam_client.detach_role_policy(
                            PolicyArn=iamPolicyArn,
                            RoleName=groupName.rstrip().title() + "Role"
                        )

                        response = iam_client.list_policy_versions(
                            PolicyArn=iamPolicyArn
                        )

                        for version in response['Versions']:
                            if version['IsDefaultVersion'] == False:
                                response = iam_client.delete_policy_version(
                                    PolicyArn=iamPolicyArn,
                                    VersionId=version['VersionId']
                                )

                        response = iam_client.delete_policy(
                            PolicyArn=iamPolicyArn
                        )
                        print(response)
                    except Exception:
                        pass

                    newPolicy = {}
                    newPolicy['Version'] = "2012-10-17"
                    newPolicy['Statement'] = existingPolicyStmt
                    print(newPolicy)
                    response = iam_client.create_policy(
                        PolicyName=iamPolicyName,
                        PolicyDocument=json.dumps(newPolicy)
                    )
                    print(response)

                    iam_client.attach_role_policy(
                        PolicyArn=iamPolicyArn,
                        RoleName=groupName.rstrip().title() + "Role"
                    )
            elif service == 'glue_catalog':

                groupNameListSplit = groupNameList.split()
                for groupName in groupNameListSplit:
                    rangerpolicyresource = resources[
                                           resources.find("values={") + len("values={"):resources.find("} isExcludes")]
                    print(rangerpolicyresource)

                    tables = keyvalues[keyvalues.find("table={"):keyvalues.find("} policyItems")]
                    rangerpolicytable = tables[tables.find("values={") + len("values={"):tables.find("} isExcludes")]
                    print(rangerpolicytable)

                    schemaList = rangerpolicyresource.split()
                    for schema in schemaList:
                        generateGlueCatalogPolicy(schema, rangerpolicytable, groupName.rstrip().title() + "Role")


def generateGlueCatalogPolicy(database, table, Iamrole):
    client = boto3.client('lakeformation')

    response = client.grant_permissions(
        Principal={
            'DataLakePrincipalIdentifier': Iamrole
        },
        Resource={
            'Table': {
                'DatabaseName': database,
                'Name': table
            }
        },
        Permissions=[
            'SELECT'
        ]
    )
    print(response)


if __name__ == "__main__":
    event = {}
    generateGlueCatalogPolicy("retail", "products", "AnalystRole")
