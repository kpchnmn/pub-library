import boto3
import base64
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import re
import os

email_path_name_length  = len(os.environ['EmailPathName'])
expires_in = os.environ['ExpiresIn']
TOPIC_ARN = os.environ['TOPIC_ARN']

s3 = boto3.resource('s3')
client = boto3.client('s3')

filenames = []
presigned_urls = [] 

def get_header(msg, name):
    header = ''
    if msg[name]:
        for tup in decode_header(str(msg[name])):
            if type(tup[0]) is bytes:
                charset = tup[1]
                if charset:
                    header += tup[0].decode(tup[1])
                else:
                    header += tup[0].decode()
            elif type(tup[0]) is str:
                header += tup[0]
    return header

def format_msg(from_,to,date,subject,msg,filenames,presigned_urls,key):
    message = '<　本メッセージは、システムより自動配信されています。＞ \n'\
                + '--------------------------------------------------------------------------------\n'\
                + '■ 送信元: %s \n'% from_\
                + '■ 送信先: %s \n'% to\
                + '■ 送信日時: %s \n'% date\
                + '■ 件名: %s \n'% subject\
                + '■ 本文: \n'\
                + '%s \n\n'% msg\
    
    print(filenames)
    print(presigned_urls)
    if len(filenames) > 0:
        message += '■ 添付ファイル\n'
        for i, filename in enumerate(filenames):
            message += '['+str(i+1)+']  %s\n'% filename
        message += '■ ダウンロードURL（有効期限: %s 時間）\n'% str(int(expires_in)/3600)
        for i,presigned_url in enumerate(presigned_urls):
            message += '['+str(i+1)+']  %s\n'% presigned_url
        
    message += '--------------------------------------------------------------------------------\n'\
                + 'このメールは、送信専用のため返信できません。\n'\
                + '有効期限後問い合わせ用ID: %s'% key[email_path_name_length:]
    
    print(message)
    return {'subject':subject,'message':message}
    
def send_to_sns(subject,message):
    
    sns = boto3.client('sns')
    
    request = {
        'TopicArn': TOPIC_ARN,
        'Subject': subject,
        'Message': message
    }
    
    response = sns.publish(**request)

def lambda_handler(event, context):
    message = ''
    html = ''
    filenames = []
    presigned_urls = [] 
    
    print("-----Event Log START-----")
    print(event)
    print("-----Event Log END-----")
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        print("Key:" + key[email_path_name_length:])
    except:
        print('error')
    try:
        response = s3.meta.client.get_object(Bucket=bucket, Key=key)
        email_body = response['Body'].read().decode('utf-8')
        email_object = email.message_from_string(email_body)
        
        from_ = get_header(email_object, 'From')
        date = get_header(email_object, 'Date')
        subject = get_header(email_object, 'Subject')
        to = get_header(email_object, 'To')
        print("送信元: " + str(from_))
        print("送信先: " + str(to))
        print("送信日時: " + str(date))
        print("件名: " + str(subject))
            
        for part in email_object.walk():
            #print(part.get_content_type())
            # ContentTypeがmultipartの場合は実際のコンテンツはさらに中のpartにあるので読み飛ばす
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get_content_type() == 'text/plain':
                charset = part.get_content_charset()
                message = part.get_payload(decode=True).decode(charset)
                continue
            if part.get_content_type() == 'text/html':
                if not message =='':
                    continue
                else:
                    charset = part.get_content_charset()
                    #print(charset)
                    html_data = part.get_payload(decode=True).decode(charset)
                    #print(html_data)
                    file = "/tmp/index.html"
                    with open(file ,"w") as f:
                        f.write(html_data)
                    html_key = "file/"+key[email_path_name_length:] + "/index.html" 
                    s3.meta.client.upload_file(file, bucket,html_key)
                    html_url = client.generate_presigned_url(
                        ClientMethod='get_object',
                        Params={
                            'Bucket': bucket,
                            'Key': html_key
                        },
                        ExpiresIn=expires_in,
                        HttpMethod='GET'
                    )
                    message = '\nこのメールはHTML形式のため次のURLからご参照ください。\n\n %s'% html_url
            # ファイル名の取得
            filename = part.get_filename()
            # ファイル名がなければ飛ばす
            if not filename:
                continue
            else:
                print(filename)
                filenames.append(filename)
                # メールフォルダ内のfileディレクトリに添付ファイルを保存する
                attach_data = part.get_payload(decode=True)
                bucket_source = s3.Bucket(bucket)

                obj_key = "file" + "/" + key[email_path_name_length:] +"/"+ filename
                obj = bucket_source.put_object(ACL='private', Body=attach_data,
                                        Key=obj_key, ContentType='text/plain')
                presigned_url = client.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': bucket,
                        'Key': obj_key
                    },
                    ExpiresIn=expires_in,
                    HttpMethod='GET'
                )
                print("署名付きURL: " + str(presigned_url))
                presigned_urls.append(presigned_url)
        
        print("本文: " + str(message))
        
        result = format_msg(from_,to,date,subject,message,filenames,presigned_urls,key)
        
        send_to_sns(result['subject'],result['message'])
        
        return 'end'
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e