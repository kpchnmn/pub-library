import json
import os
import string
import secrets
import boto3

ses_region = os.environ['ses_region']
s3_region = os.environ['s3_region']
mail_size = os.environ['mail_size']
mail_domain = os.environ['mail_domain']
bucket_name = os.environ['bucket_name']
account_id = boto3.client('sts').get_caller_identity().get('Account')
lambda_function_arn = os.environ['lambda_function_arn']
event_id = os.environ['event_id']
prefix = os.environ['prefix']
rule_set_name = os.environ['rule_set_name']

s3 = boto3.client('s3')
ses = boto3.client('ses',region_name=ses_region)

def create_mail_address():
    
    def pass_gen(size=int(mail_size)):
        chars = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(chars) for x in range(size))
    address = pass_gen()
    return {'key':address, 'address':address + mail_domain,'bucket': bucket_name + address }
    
def create_s3_bucket(bucket):
    response = s3.create_bucket(
        ACL='private',
        Bucket= bucket,
        CreateBucketConfiguration={
            'LocationConstraint': s3_region
        }
    )
    print(response)

def put_bucket_encryption(bucket):
    response = s3.put_bucket_encryption(
        Bucket = bucket,
        ServerSideEncryptionConfiguration={
            'Rules': [
                {
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256',
                    }
                },
            ]
        },
    )
    print(response)
    
def put_bucket_policy(bucket):
    
    def create_policy():
        policy = '''
        {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Sid": "AllowSESPuts",
              "Effect": "Allow",
              "Principal": {
                "Service": "ses.amazonaws.com"
              },
              "Action": "s3:PutObject",
              "Resource": "",
              "Condition": {
                "StringEquals": {
                  "aws:Referer": ""
                }
              }
            }
          ]
        }
        '''
        
        json_policy =  json.loads(policy)
        json_policy['Statement'][0]['Resource'] = 'arn:aws:s3:::'+bucket+'/*'
        json_policy['Statement'][0]['Condition']['StringEquals']['aws:Referer'] = account_id
        return json.dumps(json_policy)
        
    policy = create_policy()
    
    response = s3.put_bucket_policy(
        Bucket = bucket,
        Policy= policy,
    )
    print(response)
    

def put_bucket_notification(bucket):
    
    response = s3.put_bucket_notification_configuration(
        Bucket = bucket,
        NotificationConfiguration={
            'LambdaFunctionConfigurations': [{
                'Id': event_id,
                'LambdaFunctionArn': lambda_function_arn,
                'Events': [
                    's3:ObjectCreated:*'
                ],
                'Filter':{
                    'Key':{
                        'FilterRules':[
                            {
                                'Name':'Prefix',
                                'Value': prefix,
                            }
                            ]
                    }
                }
            }
          ]
        }
    )
    print(response)
    
def create_receipt_rule(key,email,bucket):
    
    response = ses.create_receipt_rule(
        RuleSetName= rule_set_name,
        Rule={
            'Name': key,
            'Enabled': True,
            'TlsPolicy': 'Optional',
            'Recipients': [
                email,
            ],
            'Actions': [
                {
                    'S3Action': {
                        'BucketName': bucket,
                        'ObjectKeyPrefix': prefix[:-1],
                    }
                }
            ],
            'ScanEnabled': True
        }
    )
    print(response)
    
  
def lambda_handler(event, context):
    
    # create new e-mail
    result = create_mail_address()
    result['AccountId'] = account_id
    print(result)
    
    try:
        # create new s3 bucket
        create_s3_bucket(result['bucket'])
        
        # put bucket encryption
        put_bucket_encryption(result['bucket'])
        
        # put bucket policy
        put_bucket_policy(result['bucket'])
        
        # put bucket notification
        put_bucket_notification(result['bucket'])
        
        # create receipt rule
        create_receipt_rule(result['key'],result['address'],result['bucket'])
    
    except Exception as e:
        result['Error'] = str(e)
        
    return {'message': result }