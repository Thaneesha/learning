#!/usr/bin/env python
import boto3
import botocore
import os

# Get the list of accounts for cleanup

account_list = []
role_arn = "arn:aws:iam::<account_id>:role/<cross_account_role>"
client = boto3.client('sts')
response = client.assume_role(RoleArn=role_arn, RoleSessionName="Jenkins")
credentials = response['Credentials']

Organization = boto3.client('organizations',
                            aws_access_key_id=credentials['AccessKeyId'],
                            aws_secret_access_key=credentials['SecretAccessKey'],
                            aws_session_token=credentials['SessionToken']
                            )

paginator=Organization.get_paginator("list_accounts")
page_iterator = paginator.paginate()

regions=["us-west-2","us-east-1","eu-central-1","eu-west-1"]
for page in page_iterator:
        for account in page['Accounts']:
            if account['Status'] == "ACTIVE" and account['Id'] :
                for region in regions:
                        sts_client = boto3.client('sts')
                        account_role_arn = 'arn:aws:iam::'+ account['Id']+ ':role/ROLE-SHARED-JENKINS'
                        account_response = sts_client.assume_role(RoleArn=account_role_arn, RoleSessionName='Jenkins')
                        ec2_client_creds = account_response['Credentials']
                        ec2_client = boto3.client('ec2',
                               aws_access_key_id=ec2_client_creds['AccessKeyId'],
                               aws_secret_access_key=ec2_client_creds['SecretAccessKey'],
                               aws_session_token=ec2_client_creds['SessionToken'],region_name=region
                                )
                        #ami_name = os.environ.get('ami_name')
                       ami_name = "Name of the Image"
                        ec2_client_creds
                        ami_list = ec2_client.describe_images(Owners=[account['Id']],Filters=[{'Name': 'name', 'Values': [ami_name]}])
                        if ami_list['Images'] != []:
                                print('Found AMI(s) with supplied Name')
                        for image in ami_list['Images']:
                                print('Image ID is: ', image['ImageId'])
                                image_id = image['ImageId']
                                # Dry run to check permissions
                                try:
                                        response = ec2_client.deregister_image(ImageId=image_id, DryRun=True)
                                except botocore.exceptions.ClientError as e:
                                        if 'DryRunOperation' not in str(e):
                                                raise
                                # Deregister if dry run was successful
                                try:
                                        response = ec2_client.deregister_image(ImageId=image_id, DryRun=False)
                                        http_statusCode = response['ResponseMetadata']['HTTPStatusCode']
                                        if http_statusCode == 200:
                                                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                                                print('Successfully Deregistered AMI with ID: ', image_id, 'in account: ', account['Id'],'in region:',region)
                                                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                                except botocore.exceptions.ClientError as e:
                                        print(e)
                        else:
                                print('No AMI(s) with the supplied name found in account: ', account['Id'],'in region:',region)
