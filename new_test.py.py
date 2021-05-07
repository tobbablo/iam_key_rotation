import json
import boto3
import base64
import datetime
import os
from datetime import date
from botocore.exceptions import ClientError
iam = boto3.client('iam')
secretmanager = boto3.client('secretsmanager')
# IAM_UserName=os.environ['IAM_UserName']
# SecretName=os.environ['SecretName']

def create_key(uname):
    try:
        IAM_UserName=uname
        response = iam.create_access_key(UserName=IAM_UserName)
        AccessKey = response['AccessKey']['AccessKeyId']
        SecretKey = response['AccessKey']['SecretAccessKey']
        json_data=json.dumps({'AccessKey':AccessKey,'SecretKey':SecretKey})
        secmanagerv=secretmanager.put_secret_value(SecretId=IAM_UserName,SecretString=json_data)
        emailmsg="New "+AccessKey+" has been create. Please get the secret key value from secret manager"
        ops_sns_topic = 'arn:aws:sns:us-east-1:052805659558:test'
        sns_send_report = boto3.client('sns',region_name='us-east-1')
        sns_send_report.publish(TopicArn=ops_sns_topic, Message=emailmsg, Subject="New Key created for user"+ IAM_UserName)
    except ClientError as e:
        print (e)

def deactive_key(uname):
    try:
	    #GET PREVIOUS AND CURRENT VERSION OF KEY FROM SECRET MANAGER
        IAM_UserName=uname
        getpresecvalue=secretmanager.get_secret_value(SecretId=IAM_UserName,VersionStage='AWSPREVIOUS')
        getcursecvalue=secretmanager.get_secret_value(SecretId=IAM_UserName,VersionStage='AWSCURRENT')
        print (getpresecvalue)
        print (getcursecvalue)
        preSecString = json.loads(getpresecvalue['SecretString'])
        print(preSecString)
        preAccKey=preSecString['AccessKey']
        #GET CREATION DATE OF CURRENT VERSION OF ACCESS KEY
        curdate=getcursecvalue['CreatedDate']
        #GET TIMEZONE FROM CREATION DATE
        tz=curdate.tzinfo
        #CALCULATE TIME DIFFERENCE BETWEEN CREATION DATE AND TODAY
        diff=datetime.datetime.now(tz)-curdate
        diffdays=diff.days
        #print (curdate)
        #print (tz)
        #print (diffdays)
        #print (preAccKey)
        topic=''
        #IF TIME DIFFERENCE IS MORE THAN x NUMBER OF DAYS THEN DEACTIVATE PREVIOUS KEY AND SEND A MESSAGE
        if diffdays >= 1:
            iam.update_access_key(AccessKeyId=preAccKey,Status='Inactive',UserName=IAM_UserName)
            topic.append('deactivated')
        emailmsg="PreviousKey "+preAccKey+" has been disabled for IAM User"+IAM_UserName
        ops_sns_topic ='arn:aws:sns:us-east-1:052805659558:test'
        sns_send_report = boto3.client('sns',region_name='us-east-1')
        sns_send_report.publish(TopicArn=ops_sns_topic, Message=emailmsg, Subject='Previous Key {0}'.format(topic))
    #   else:
    #         print ("Current Key is not older than 10 days")
        return
    except ClientError as e:
        print (e)
   
    # print (diffdays)

def delete_key(uname):
    try:
        IAM_UserName=uname
        print (IAM_UserName)
        getpresecvalue=secretmanager.get_secret_value(SecretId=IAM_UserName,VersionStage='AWSPREVIOUS')
        getcursecvalue=secretmanager.get_secret_value(SecretId='secmanager3',VersionStage='AWSCURRENT')
        preSecString = json.loads(getpresecvalue['SecretString'])
        preAccKey=preSecString['AccessKey']
        print (preAccKey)
    #GET CREATION DATE OF CURRENT VERSION OF ACCESS KEY
        curdate=getcursecvalue['CreatedDate']
    #GET TIMEZONE FROM CREATION DATE
        tz=curdate.tzinfo
    #CALCULATE TIME DIFFERENCE BETWEEN CREATION DATE AND TODAY
        diff=datetime.datetime.now(tz)-curdate
        diffdays=diff.days
    #IF TIME DIFFERENCE IS MORE THAN x NUMBER OF DAYS THEN DEACTIVATE PREVIOUS KEY AND SEND A MESSAGE
        if diffdays >= 1:
         keylist=iam.list_access_keys (UserName=IAM_UserName)
        print (keylist)
        for x in range(2):
            prevkeystatus=keylist['AccessKeyMetadata'][x]['Status']
            preacckeyvalue=keylist['AccessKeyMetadata'][x]['AccessKeyId']
            print (prevkeystatus)
            if prevkeystatus == "Inactive": 
                 if preAccKey==preacckeyvalue:
                    print (preacckeyvalue)
                    iam.delete_access_key (UserName=IAM_UserName,AccessKeyId=preacckeyvalue)
                    emailmsg="PreviousKey "+preacckeyvalue+" has been deleted for user"+IAM_UserName
                    ops_sns_topic ='arn:aws:sns:us-east-1:052805659558:test'
                    sns_send_report = boto3.client('sns',region_name='us-east-1')
                    sns_send_report.publish(TopicArn=ops_sns_topic, Message=emailmsg, Subject='Previous Key has been deleted')
                    return
            else:
                    print ("secret manager previous value doesn't match with inactive IAM key value")
        else:
              print ("previous key is still active")
        return
    except ClientError as e:
        print (e)
    else:
        print ("Current Key is not older than 10 days")
    
def lambda_handler(event, context):
    # TODO implement
    faction=event ["action"]
    fuser_name=event ["username"]
    if faction == "create":
        status = create_key(fuser_name)
        print (status)
    elif faction == "deactivate":
        status = deactive_key(fuser_name)
        print (status)
    elif faction == "delete":
        status = delete_key(fuser_name)
        print (status)