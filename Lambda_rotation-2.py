import boto3
import json

from datetime import datetime,timezone
from botocore.exceptions import ClientError
from os import environ

ops_sns_topic = environ['SNS_TOPIC_ARN']
today = datetime.now(timezone.utc)
iam = boto3.client('iam')
secretmanager = boto3.client('secretsmanager')

def create_key(uname):
    try:
        IAM_UserName=uname
        response = iam.create_access_key(UserName=IAM_UserName)
        AccessKey = response['AccessKey']['AccessKeyId']
        SecretKey = response['AccessKey']['SecretAccessKey']
        json_data=json.dumps({'AccessKey' :AccessKey, 'SecretKey' :SecretKey})
        response = secretmanager.create_secret(Name=IAM_UserName)
        secmanagerv=secretmanager.put_secret_value(SecretId=IAM_UserName,SecretString=json_data)
        print(" A Secret was created for " + IAM_UserName + ' and the access and secret has been dumped there')
        emailmsg= "New "+AccessKey+" has been created. Please get the secret value from secret manager"
        sns_send_report = boto3.client('sns',region_name='us-west-2')
        sns_send_report.publish(TopicArn=ops_sns_topic, Message=emailmsg, Subject ="New Key created for user"+  IAM_UserName)
    except ClientError as e:
        print("I Couldnt create any access key right now. See Error below")
        print (e)
accesskey_list=[]
past_90_keys_list=[]


def check_for_expired_keys():
    iam_users=iam.list_users().get('Users')
    for u in iam_users:
        uname=u.get('UserName')
        user_key_details=iam.list_access_keys(UserName=uname).get('AccessKeyMetadata')
        if len(user_key_details)== 1:            
            user_key_details=user_key_details[0]
            user_key_created_date=user_key_details.get('CreateDate')
            user_access_key=user_key_details.get('AccessKeyId')
            length_keys= str(today - user_key_created_date)
            
            if 'day' in length_keys:
                len_keys_days=length_keys.split('day')[0]
                if int(len_keys_days)>= 1:
                    past_90_keys_dict={'uname':uname, 'access':user_access_key}
                    past_90_keys_list.append(past_90_keys_dict)
            
        elif len(user_key_details)== 2:
            user_key_details1=user_key_details[0]
            user_key_details2=user_key_details[1]
            user_key_created_date1=user_key_details1.get('CreateDate')
            user_key_created_date2=user_key_details2.get('CreateDate')
            len_days_diff = user_key_created_date2 - user_key_created_date1
            user_access_key1=user_key_details1.get('AccessKeyId')
            user_access_key2=user_key_details2.get('AccessKeyId')
            access_key1_status=user_key_details1.get('Status')
            access_key2_status=user_key_details2.get('Status')
            if 'days' in str(len_days_diff):
                print("Wow! " + uname + ' has 2 access keys created on different days and their difference is ' + str(len_days_diff))
                len_days_diff=str(len_days_diff).split('days')[0]
                if 0 < abs(int(len_days_diff)) < 90: 
                    pass
                elif 90 <= abs(int(len_days_diff)) < 100: 
                    if user_key_created_date2 > user_key_created_date1:
                        iam.update_access_key(AccessKeyId=user_access_key1, Status='Inactive', UserName=uname)
                    else:
                        iam.update_access_key(AccessKeyId=user_access_key2, Status='Inactive', UserName=uname)
                elif abs(int(len_days_diff)) >= 90:
                    print (' One of ' + uname + ' key stand a chance of deletion')
                    if user_key_created_date2 > user_key_created_date1 and access_key2_status == 'Active' and access_key1_status == 'Inactive' :
                        iam.delete_access_key(AccessKeyId=user_access_key1, UserName=uname)
                    elif user_key_created_date1 > user_key_created_date2 and access_key1_status == 'Active' and access_key2_status == 'Inactive' :
                        iam.delete_access_key(AccessKeyId=user_access_key2, UserName=uname)
                    else:
                        print( " I am sorry, i cannot Delete Any keys now because one of the latest keys might be inactive and that will cause a lot of damage")
        else:
            pass
    return past_90_keys_list


past_90_days_keys=check_for_expired_keys()

def createkeyForPast90(acccess_keys_list):
    for ak in acccess_keys_list:
        uname=ak.get('uname')
        faction='create'
        fuser_name=uname
        if faction == "create":
            print("I will be creating secret and access keys for " + fuser_name + " and I will be storing them in Secret manager" )
            status = create_key(fuser_name)
            print (status)
        elif faction == "deactivate":
            status = deactive_key(fuser_name)
            print (status)
        elif faction == "delete":
            status = delete_key(fuser_name)
            print (status)

def lambda_handler(event, context):
    past_90_days_keys=check_for_expired_keys()
    createkeyForPast90(past_90_days_keys)
    
    
