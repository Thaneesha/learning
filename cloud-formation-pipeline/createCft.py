#!/usr/bin/python3
import sys
import os
import configparser
import boto3
from subprocess import Popen, PIPE
from botocore.exceptions import ClientError

try:
    config_file = sys.argv[1]
except BaseException:
    print('Failed to parse config file as input')
    sys.exit(1)

cfg = configparser.ConfigParser()
cfg.read(config_file)
##########Getting account values from config file########
account_name = cfg.get('account', 'account_name')
action = cfg.get('account', 'action')
region = cfg.get('account', 'region')
cloud_formation_template_path = cfg.get(
    'account', 'cloud_formation_template_path')
profile = cfg.get('account', 'profile')
DevOpsAccountId = cfg.get('account', 'DevOpsAccountId')
LoggingAccountId = cfg.get('account', 'LoggingAccountId')

##########Getting tag values from config file#########
organization = cfg.get('tags', 'organization')
function = cfg.get('tags', 'function')
environment = cfg.get('tags', 'environment')
version_number = cfg.get('tags', 'version_number')
contact = cfg.get('tags', 'contact')
lifetime = cfg.get('tags', 'lifetime')

##########Variables for stack creation###############
s3_temp_bucket = "lsg-bio-del"
#s3_temp_bucket = "lsg-" + account_name + "-account-onboarding-templates"
storageclass = "Glacier"
transitiondays = "90"
stackname = "lsg-" + account_name + "-account-onboarding"
cloudformation_template_tag = stackname
cft_name = "lsg-" + account_name + "-account-onboarding.yml"

templateurl = "https://s3." + region + \
    ".amazonaws.com/" + s3_temp_bucket + "/" + cft_name
print('Cloud formation template URL', templateurl)


def commit_id():
    cmd = "git rev-parse HEAD"
    p = Popen(cmd, shell=True, stdout=PIPE, universal_newlines=True)
    str = p.communicate()[0]
    return str.strip()


def create_stack():
    session = boto3.session.Session(profile_name=profile)
    cloudformation = session.client('cloudformation', region_name=region)
    commit = commit_id()
    try:
        stack = cloudformation.create_stack(
            StackName=stackname,
            TemplateURL=templateurl,
            Parameters=[
                {'ParameterKey': 'S3TempBucket', 'ParameterValue': s3_temp_bucket},
                {'ParameterKey': 'StorageClass', 'ParameterValue': storageclass},
                {'ParameterKey': 'TransitionDays',
                    'ParameterValue': transitiondays},
                {'ParameterKey': 'DevOpsAccountId',
                    'ParameterValue': DevOpsAccountId},
                {'ParameterKey': 'LoggingAccountId',
                    'ParameterValue': LoggingAccountId},
                {'ParameterKey': 'AccountName', 'ParameterValue': account_name},
            ],
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            Tags=[
                {'Key': 'organization', 'Value': organization},
                {'Key': 'cloudformation-template',
                 'Value': cloudformation_template_tag},
                {'Key': 'function', 'Value': function},
                {'Key': 'name', 'Value': account_name},
                {'Key': 'environment', 'Value': environment},
                {'Key': 'version-number', 'Value': version_number},
                {'Key': 'commit', 'Value': commit},
                {'Key': 'contact', 'Value': contact},
                {'Key': 'lifetime', 'Value': lifetime}
            ],
            OnFailure='DO_NOTHING'
        )
        print('Creating stack with name: ' + stackname)
        print('Stack creation running...waiting for completion')
        waiter = cloudformation.get_waiter('stack_create_complete')
        waiter.wait(StackName=stackname)
        print('Stack Created')
    except ClientError as e:
        print('Stack creation failed %s' + e.response['Error']['Code'])


def describe_stack():
    session = boto3.session.Session(profile_name=profile)
    cloudformation = session.client('cloudformation')
    describe_response = cloudformation.describe_stacks(StackName=stackname)
    print('Status of the stack ' + stackname + ' is ' +
          describe_response['Stacks'][0]['StackStatus'])


def delete_stack():
    session = boto3.session.Session(profile_name=profile)
    cloudformation = session.client('cloudformation')
    try:
        stack = cloudformation.delete_stack(StackName=stackname)
        print('Deleting the stack with name: ' + stackname)
        print('Stack deletion running...waiting for completion')
        waiter = cloudformation.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stackname)
        print('Stack Deleted')
    except ClientError as e:
        print('Stack deletion failed %s' + e.response['Error']['Code'])


def update_stack():
    session = boto3.session.Session(profile_name=profile)
    cloudformation = session.client('cloudformation')
    commit = commit_id()
    try:
        stack = cloudformation.update_stack(
            StackName=stackname,
            TemplateURL=templateurl,
            Parameters=[
                {'ParameterKey': 'S3TempBucket', 'ParameterValue': s3_temp_bucket},
                {'ParameterKey': 'StorageClass', 'ParameterValue': storageclass},
                {'ParameterKey': 'TransitionDays',
                    'ParameterValue': transitiondays},
                {'ParameterKey': 'DevOpsAccountId',
                    'ParameterValue': DevOpsAccountId},
                {'ParameterKey': 'LoggingAccountId',
                    'ParameterValue': LoggingAccountId},
                {'ParameterKey': 'AccountName', 'ParameterValue': account_name}
            ],
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            Tags=[
                {'Key': 'organization', 'Value': organization},
                {'Key': 'cloudformation-template',
                 'Value': cloudformation_template_tag},
                {'Key': 'function', 'Value': function},
                {'Key': 'name', 'Value': account_name},
                {'Key': 'environment', 'Value': environment},
                {'Key': 'version-number', 'Value': version_number},
                {'Key': 'commit', 'Value': commit},
                {'Key': 'contact', 'Value': contact},
                {'Key': 'lifetime', 'Value': lifetime}
            ]
        )
        print('Updating the stack with name: ' + stackname)
        print('Stack update running...waiting for completion')
        waiter = cloudformation.get_waiter('stack_update_complete')
        waiter.wait(StackName=stackname)
        print('Stack Updated')
    except ClientError as e:
        print('Stack update failed %s' + e.response['Error']['Code'])


def sync_s3(s3_temp_bucket_name, cft_dir, profile, region):
    if not os.path.isdir(cft_dir):
        raise ValueError('cft_dir %r not found.' % cft_dir)
    session = boto3.session.Session(profile_name=profile, region_name=region)
    s3 = session.client('s3')
    try:
        s3.head_bucket(Bucket=s3_temp_bucket_name)
        print(
            'Bucket ',
            s3_temp_bucket_name,
            ' already exists. Copying the template files')
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            try:
                print("Creating Bucket")
                bucket = s3.create_bucket(
                    Bucket=s3_temp_bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': region})
            except ClientError as e:
                print('Bucket creation failed' + e.response['Error']['Code'])
    uploadFileNames = []
    for root, dirs, files in os.walk(cft_dir, topdown=False):
        for name in files:
            fname=os.path.join(root, name)
            uploadFileNames.append(fname)
    sys.exit(1)
    for filename in uploadFileNames:
        sourcepath = filename
        s3.upload_file(filename,s3_temp_bucket_name,filename)

if __name__ == '__main__':
    # Create S3 bucket to have latest templates or copy the templates if
    # bucket already exists
    sync_s3(s3_temp_bucket, cloud_formation_template_path, profile, region)
    sys.exit(1)
    if action == "create-stack":
        create_stack()
    elif action == "delete-stack":
        delete_stack()
    elif action == "update-stack":
        update_stack()
    elif action == "describe-stack":
        describe_stack()
